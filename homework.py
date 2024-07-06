import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from exceptions import ApiError
from telebot import TeleBot


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter('%(asctime)s, %(levelname)s, %(message)s, %(name)s')
)
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        logging.critical('Отсутствуют переменные окружения.')


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Сообщение успешно отправдено: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception as error:
        logging.error(f'Не удалось получить доступ к API: {error}')
        raise ApiError

    if response.status_code != HTTPStatus.OK:
        raise requests.HTTPError(response)

    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Тип данных не является словарём.')
        raise TypeError('Тип данных не является словарём.')

    response = response.get('homeworks')

    if not isinstance(response, list):
        logging.error('Тип данных не является списком.')
        raise TypeError('Тип данных не является списком.')

    return response


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ не найден.')
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    except KeyError:
        logging.error('Ключ не найден.')
        raise KeyError('Ключ не найден.')

    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError:
        logging.debug('Неизвестный статус.')
        raise KeyError('Неизвестный статус.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    if check_tokens():
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)

                if homeworks:
                    message = parse_status(homeworks[0])
                else:
                    message = 'Пока ничего нового.'
                send_message(bot, message)
                current_timestamp = int(time.time())

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)

            finally:
                time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
