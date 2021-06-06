import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from json.decoder import JSONDecodeError
from telegram import bot

load_dotenv()

PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[RotatingFileHandler(
        os.path.join(PATH, 'logger.log'), maxBytes=50000000, backupCount=5
    )]
)

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.exception('Environment variable not found')
    sys.exit(1)

URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        logging.error('Homework_name or status are not available')
        send_message('Homework_name or status are not available', bot)
        return 'No data available, server error'
    status_changed = 'Изменен статус работы'
    status_completed = 'У вас проверили работу'
    statuses = {
        'reviewing': (status_changed, 'Работа взята в ревью.'),
        'rejected': (
            status_completed, 'К сожалению в работе нашлись ошибки.'
        ),
        'approved': (
            status_completed,
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.')
    }
    message, verdict = statuses[status]
    if status not in statuses:
        logging.error('Unknown homework status error')
        send_message('Unknown homework status error', bot)
        return 'Unknown status error'
    return f'{message} "{homework_name}"\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as req_error:
        logging.exception(f'Connection error: {req_error}')
        send_message(f'Connection error: {req_error}', bot)
    except JSONDecodeError as json_error:
        logging.exception(f'json conversion error: {json_error}')
        send_message(f'json conversion error: {json_error}', bot)
    return homework_statuses.json()


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except requests.exceptions.RequestException as e:
        logging.exception(f'Sending message error: {e}')


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Bot initializing message')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            last_homework = new_homework.get('homeworks')[0]
            if last_homework:
                status_message = parse_homework_status(last_homework)
                send_message(status_message, bot)
                logging.info('Message sending completed')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            logging.exception(f'Bot startup error: {e}')
            send_message(f'Bot startup error: {e}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
