import telebot
import gspread
import traceback
import re
import os
from dotenv import load_dotenv

load_dotenv()  # Загрузка переменных окружения из .env файла
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Замените на токен вашего бота или добавьте в .env
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Замените на ID вашей Google таблицы (только ID) или добавьте в .env
SHEET_NAME = os.getenv("SHEET_NAME", "Тест")  # Замените на название листа в таблице или добавьте в .env, по умолчанию "Тест"
CHAT_ID = os.getenv("CHAT_ID")  # Замените на ID чата, откуда бот будет читать сообщения или добавьте в .env
CREDENTIALS_FILE = 'YOUR_CREDENTIALS_FILE.json'


# --- Авторизация в Google Sheets ---
scope = [
       'https://www.googleapis.com/auth/spreadsheets',
       'https://www.googleapis.com/auth/drive'
   ]

gc = gspread.service_account(filename=CREDENTIALS_FILE, scopes=scope)
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# --- Инициализация бота ---
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- Обработчик команды /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("Команда /start получена!")  # Добавлено для отладки
    bot.reply_to(message, "Привет! Я бот для формирования реестра оплат. Отправляйте сообщения в формате дата - ")

def find_empty_row(worksheet, date_column=1):  # date_column - номер столбца с датой (начинается с 1)
    """Находит первую строку, где столбец с датой пуст."""
    data = worksheet.col_values(date_column)
    try:
        empty_row_index = data.index('') + 1  # Индекс первой пустой ячейки + 1 = номер строки
        return empty_row_index
    except ValueError:
        return len(data) + 1  # Если все ячейки заполнены, возвращает номер следующей строки

# --- Функция для обработки сообщений ---
@bot.message_handler(func=lambda message: str(message.chat.id) in CHAT_ID)
def handle_message(message):
        text = message.text
        if text.startswith('@paycollect_bot'):
            try:
                text = text.lstrip('@paycollect_bot').strip()
                text = [item.strip() for item in text.split('-')]
                errors = []  # Список для хранения сообщений об ошибках

                # Проверяем каждую часть текста с помощью регулярных выражений
                if not re.match(r"\d{2}\.\d{2}\.\d{4}", text[0]):  # Проверяем дату
                    errors.append('Ошибка в дате')
                if not re.match(r"[\w\s.,*-]+", text[1]):  # Проверяем название объекта
                    errors.append('Ошибка в названии объекта')
                if not re.match(r"[\w\s]+", text[2]):  # Проверяем регион
                    errors.append('Ошибка в регионе')
                if not re.match(r"[\w\s]+", text[3]):  # Проверяем этап/вид расходов
                    errors.append('Ошибка в категории этапе/виде расходов')
                if not re.match(r"[\w\s]+", text[4]):  # Проверяем описание
                    errors.append('Ошибка в описании')
                if not re.match(r"[\w\s.,*-]+", text[5]):  # Проверяем детализацию расходов
                    errors.append('Ошибка в детализации расходов')
                if not re.match(r"^\d+$", text[6]): # Проверяем сумму
                    errors.append('Ошибка в сумме: некорректный формат (только цифры)')
                if not re.match(r"[\w\s.,*-]+", text[7]):  # Проверяем поставщика
                    errors.append('Ошибка в поставщике')
                if not re.match(r"[\w\s]+", text[8]):  # Проверяем компанию
                    errors.append('Ошибка в компании')

                # Выводим ошибки, если они есть
                if errors:
                    for error in errors:
                        bot.reply_to(message, f"{error}")
                else:
                    date, project, direction, stage, category, description, amount, supplier, company = tuple(text)
                    row = [
                        date, project.strip(), '', direction.strip().title(), stage, category.strip(),
                        description.strip(), amount,
                        supplier.strip(), f"https://t.me/c/2890383045/{message.message_id}", company.strip()]
                    empty_row = find_empty_row(worksheet)

                    if empty_row is not None and empty_row <= worksheet.row_count:

                        for i, value in enumerate(row):
                            worksheet.update_cell(empty_row, i + 1, value)  # i + 1 = номер столбца
                    else:
                        bot.reply_to(message, "Не найдена строка без даты. Данные не были записаны.")

                    bot.reply_to(message, "Данные успешно добавлены в Google Sheets!")

            except IndexError as e:
                bot.reply_to(message, f"Отсутствуют обязательные поля для заполнения")
            except Exception as e:
                bot.reply_to(message, f"Произошла ошибка при обработке сообщения: {e}")
                print(f"Ошибка: {e}")
                traceback.print_exc()  # Выводим traceback
                print(f"Текст сообщения: {text}")

# --- Запуск бота ---
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()