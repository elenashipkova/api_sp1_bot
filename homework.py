import logging
import os
import sys
import time
from json.decoder import JSONDecodeError
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PATH, 'logger.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[RotatingFileHandler(
        LOG_FILE, maxBytes=50000000, backupCount=5
    )]
)

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as e:
    logging.exception(f'Environment variable not found: {e}')
    sys.exit(1)

URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
STATUS_CHANGED = 'Изменен статус работы'
STATUS_COMPLETED = 'У вас проверили работу'
STATUSES = {
    'reviewing': (STATUS_CHANGED, 'Работа взята в ревью.'),
    'rejected': (
        STATUS_COMPLETED, 'К сожалению в работе нашлись ошибки.'
    ),
    'approved': (
        STATUS_COMPLETED,
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    )
}
ERRORS = {
    'server': 'Server connection error',
    'json': 'JSON decoding error',
    'bot': 'Bot initializing error',
    'data_is_none': 'Homework_name or status are not available',
    'unknown_status': 'Unknown homework status error',
    'message': 'Bot sending message error',
    'function': 'Function execution error'
}


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        logging.error(ERRORS['data_is_none'])
        return ERRORS['data_is_none']
    if status not in STATUSES:
        logging.error(ERRORS['unknown_status'])
        return ERRORS['unknown_status']
    message, verdict = STATUSES[status]
    return f'{message} "{homework_name}"\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as req_error:
        logging.exception(f"{ERRORS['server']}: {req_error}")
        return {'error': ERRORS['server'] + req_error}
    try:
        return homework_statuses.json()
    except JSONDecodeError as json_error:
        logging.exception(f"{ERRORS['json']}: {json_error}")
        return {'error': ERRORS['json'] + json_error}


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except requests.exceptions.RequestException as e:
        logging.exception(f"{ERRORS['message']}: {e}")


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Bot initializing message')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('error'):
                send_message(
                        f"{ERRORS['function']} {get_homework_statuses}", bot)
                time.sleep(5)
                continue
            last_homework = new_homework.get('homeworks')
            if last_homework:
                status_message = parse_homework_status(last_homework[0])
                send_message(status_message, bot)
                logging.info(f'Message sending completed: {status_message}')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            logging.exception(f"{ERRORS['bot']}: {e}")
            send_message(f"{ERRORS['bot']}: {e}", bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
