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
SERVER_ERROR = 'Server connection error'
JSON_ERROR = 'JSON decoding error'
BOT_ERROR = 'Bot initializing error'
DATA_IS_NONE = 'Homework_name or status are not available'
UNKNOWN_STATUS_ERROR = 'Unknown homework status error'
MESSAGE_ERROR = 'Bot sending message error'
FUNCTION_ERROR = 'Function execution error'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        logging.error(DATA_IS_NONE, exc_info=True)
        return DATA_IS_NONE
    if status not in STATUSES:
        logging.error(UNKNOWN_STATUS_ERROR, exc_info=True)
        return UNKNOWN_STATUS_ERROR
    message, verdict = STATUSES[status]
    return f'{message} "{homework_name}"\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as req_error:
        logging.exception(f'{SERVER_ERROR}: {req_error}')
        return SERVER_ERROR
    try:
        return homework_statuses.json()
    except JSONDecodeError as json_error:
        logging.exception(f'{JSON_ERROR}: {json_error}')
        return JSON_ERROR


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except requests.exceptions.RequestException as e:
        logging.exception(f'{MESSAGE_ERROR}: {e}')


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Bot initializing message')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework == SERVER_ERROR or JSON_ERROR:
                send_message(f'{FUNCTION_ERROR} {get_homework_statuses}', bot)
                return f'{FUNCTION_ERROR}: {get_homework_statuses}'
            last_homework = new_homework.get('homeworks')[0]
            if last_homework:
                status_message = parse_homework_status(last_homework)
                send_message(status_message, bot)
                logging.info(f'Message sending completed: {status_message}')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            logging.exception(f'{BOT_ERROR}: {e}')
            send_message(f'{BOT_ERROR}: {e}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
