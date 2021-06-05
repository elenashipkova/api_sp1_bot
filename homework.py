import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.join(PATH, 'logger.log'),
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[RotatingFileHandler(
        os.path.join(PATH, 'logger.log'), maxBytes=50000000, backupCount=5
    )]
)
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    os.path.join(PATH, 'logger.log'), maxBytes=50000000, backupCount=5
)
logger.addHandler(handler)

try:
    os.environ['PRAKTIKUM_TOKEN']
    os.environ['TELEGRAM_TOKEN']
    os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.exception('Environment variable not found')

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        return 'No data available, server error'
    statuses = {
        'reviewing': 'Работа взята в ревью.',
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': ('Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
    }
    if status not in statuses:
        logging.exception('Unknown status')
    verdict = statuses[status]
    if status == 'reviewing':
        return f'Изменен статус работы "{homework_name}"\n\n{verdict}'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params=params)
        return homework_statuses.json()
    except requests.exceptions.RequestException as req_error:
        logging.exception(f'Connection error: {req_error}')


def send_message(message, bot_client):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except requests.exceptions.RequestException as e:
        logging.exception(f'Sending message error: {e}')


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                last_homework = new_homework.get('homeworks')[0]
                status_message = parse_homework_status(last_homework)
                send_message(status_message, bot)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            logging.exception(f'Bot startup error: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
