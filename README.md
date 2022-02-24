# Telegram-бот для проверки статуса домашнего задания(проектов) в Яндекс.Практикуме
## Краткое описание

Телеграм-бот обращается к API сервиса Практикум.Домашка и получает статус моей работы: статус работы изменяется при взятии ревьюером ее на проверку и по окончании проверки. При обновлении статуса бот отправляет вам соответствующее уведомление в Telegram. Также настроено логирование и сообщение о важных проблемах (уровня ERROR) в Telegram.

## Технологии

 - Python 3
 - python-telegram-bot 12.7
 - requests 2.23.0
 - python-dotenv==0.13.0

## Описание работы

Программы состоит из следующих функций:

 - get_homework_statuses(): посылает запрос к эндпойнту API Практикум.Домашки, возвращает информацию о последнем проекте, отправленном на ревью
 - parse_homework_status(): извлекает из информации о проекте его текущий статус и название
 - send_message(): отправляет сообщение в телеграм

Необходимо создать файл .env с переменными окружения:
```
TELEGRAM_TOKEN=
PRAKTIKUM_TOKEN=
TELEGRAM_CHAT_ID=
```
Бот размещен на Heroku. Для работы бота также необходимо сохранить переменные окружения в настройках Config Vars в Heroku.
