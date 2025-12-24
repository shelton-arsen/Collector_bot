import telebot
import gspread
import traceback
import re
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()  # Загрузка переменных окружения из .env файла
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Замените на токен вашего бота или добавьте в .env
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Замените на ID вашей Google таблицы (только ID) или добавьте в .env
SHEET_ADMIN_NAME = os.getenv("SHEET_ADMIN_NAME", "Админ бот")  # Лист для админ бота
SHEET_SNAB_NAME = os.getenv("SHEET_SNAB_NAME", "СНАБ бот текущий")  # Лист для снаб бота
CHAT_ADMIN_ID = os.getenv("CHAT_ADMIN_ID", "")  # ID чатов админ бота
CHAT_SNAB_ID = os.getenv("CHAT_SNAB_ID", "")  # ID чатов снаб бота
CREDENTIALS_FILE = 'your_credentials_file.json'


# --- Авторизация в Google Sheets ---
scope = [
       'https://www.googleapis.com/auth/spreadsheets',
       'https://www.googleapis.com/auth/drive'
   ]

gc = gspread.service_account(filename=CREDENTIALS_FILE, scopes=scope)
sh = gc.open_by_key(SPREADSHEET_ID)
# Листы инициализируются динамически в зависимости от чата

# --- Инициализация бота ---
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- Обработчик команды /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info(f"🚀 Команда /start от пользователя {message.from_user.username} ({message.from_user.id}) в чате {message.chat.id}")
    welcome_msg = "👋 Привет! Я бот для формирования реестра оплат.\n\n📋 Отправляйте сообщения в формате:\n@paycollect_bot [данные через пробел дефис пробел]\n\n💡 Используйте /info для получения шаблона"
    bot.reply_to(message, welcome_msg)
    logger.info("✅ Отправлено приветственное сообщение")

# --- Обработчик команды /info ---
@bot.message_handler(commands=['info'])
def send_info(message):
    logger.info(f"ℹ️ Команда /info от пользователя {message.from_user.username} ({message.from_user.id}) в чате {message.chat.id}")
    info_msg = """📝 Пример для описания счетов:

@paycollect_bot 01.01.2025 - Счет 1 от 01.01.2025 - Объект2 - Стройка МСК - Этап 3 - Оплата за окна - Оплата за окна алюминий - 30500,00 - ООО Петрович - ООО Дом Газобетон

🔹 Формат: дата - реквизиты счета - объект - регион - этап - категория - описание - сумма - поставщик - компания
🔹 Разделитель: пробел дефис пробел (' - ')
🔹 Сумма: только цифры без пробелов и копейки разделенные запятой"""
    bot.reply_to(message, info_msg)
    logger.info("✅ Отправлена информация о формате")

def find_empty_row(worksheet, date_column=1):  # date_column - номер столбца с датой (начинается с 1)
    """Находит первую строку, где столбец с датой пуст."""
    data = worksheet.col_values(date_column)
    try:
        empty_row_index = data.index('') + 1  # Индекс первой пустой ячейки + 1 = номер строки
        return empty_row_index
    except ValueError:
        return len(data) + 1  # Если все ячейки заполнены, возвращает номер следующей строки

# --- Функция для обработки сообщений ---
def is_authorized_chat(message):
    """Проверяет, авторизован ли чат для работы с ботом"""
    chat_id_str = str(message.chat.id)
    admin_chats = [id.strip() for id in CHAT_ADMIN_ID.split(',') if id.strip()]
    snab_chats = [id.strip() for id in CHAT_SNAB_ID.split(',') if id.strip()]

    is_in_allowed_groups = chat_id_str in admin_chats or chat_id_str in snab_chats
    
    logger.info(f"🔍 Проверка авторизации чата {chat_id_str} (тип: {message.chat.type})")
    logger.info(f"   📋 В разрешенных группах: {is_in_allowed_groups}")
    
    return is_in_allowed_groups

def get_worksheet_for_chat(chat_id):
    """Определяет лист для записи в зависимости от чата"""
    chat_id_str = str(chat_id)
    admin_chats = [id.strip() for id in CHAT_ADMIN_ID.split(',') if id.strip()]
    
    # Личные чаты направляем в админ лист для тестирования
    if chat_id_str in admin_chats:
        logger.info(f"📝 Админ группа {chat_id_str} -> Админ лист")
        return sh.worksheet(SHEET_ADMIN_NAME)
    else:
        logger.info(f"📝 Снаб группа {chat_id_str} -> Снаб лист")
        return sh.worksheet(SHEET_SNAB_NAME)

@bot.message_handler(func=is_authorized_chat, content_types=['text', 'document', 'photo', 'video'])
def handle_message(message):
    """Обработчик сообщений с полным логированием"""
    
    # Логируем получение сообщения
    logger.info(f"📩 Получено сообщение от пользователя {message.from_user.username} ({message.from_user.id}) в чате {message.chat.id}")
    logger.info(f"📝 Тип сообщения: {message.content_type}")
    
    try:
        text = None
        
        # Извлекаем текст из сообщения
        if message.content_type == 'text':
            text = message.text
            logger.info(f"💬 Текст сообщения: {text}")
        elif message.content_type == 'document' and message.caption:
            text = message.caption
            logger.info(f"📎 Описание документа: {text}")
        elif message.content_type == 'photo' and message.caption:
            text = message.caption
            logger.info(f"🖼️ Описание фото: {text}")
        elif message.content_type == 'video' and message.caption:
            text = message.caption
            logger.info(f"🎥 Описание видео: {text}")
        
        # Проверяем, что текст содержит команду бота
        if text and text.startswith('@paycollect_bot'):
            logger.info("🤖 Обрабатываем команду @paycollect_bot")
        
            # Парсим сообщение
            parsed_text = text.lstrip('@paycollect_bot').strip()
            logger.info(f"🔄 Обработанный текст: {parsed_text}")
        
            # Разбиваем на части
            try:
                parts = [item.strip() for item in parsed_text.split('-')]
                logger.info(f"📊 Разбито на {len(parts)} частей: {parts}")
            
                if len(parts) != 10:
                    error_msg = f"❌ Неверное количество полей: ожидается 10, получено {len(parts)}"
                    logger.error(error_msg)
                    bot.reply_to(message, f"Ошибка: {error_msg}. Проверьте формат сообщения и разделители.")
                    return
                
            except Exception as e:
                error_msg = f"❌ Ошибка парсинга сообщения: {str(e)}"
                logger.error(error_msg)
                bot.reply_to(message, f"Ошибка парсинга: {error_msg}")
                return
        
            # Валидация полей
            logger.info("✅ Начинаем валидацию полей...")
            errors = []
        
            # Проверяем каждое поле
            validations = [
                (r"\d{2}\.\d{2}\.\d{4}", parts[0], "Дата (ДД.ММ.ГГГГ)"),
                (r"[\w\s.,*-]+", parts[1], "Реквизиты счета"),
                (r"[\w\s.,*-]+", parts[2], "Название чата"),
                (r"[\w\s.,*-]+", parts[3], "Регион/направление"),
                (r"[\w\s.,*-]+", parts[4], "Этап/вид расходов"),
                (r"[\w\s.,*-]+", parts[5], "Категория"),
                (r"[\w\s0-9.,*-]+", parts[6], "Детализация расходов"),
                (r"^-?\d+,\d{2}$", parts[7], "Сумма (ожидается только цифры и копейки разделенные запятой)"),
                (r"[\w\s.,*-]+", parts[8], "Поставщик"),
                (r"[\w\s.,*-]+", parts[9], "Компания")
            ]
        
            for pattern, value, field_name in validations:
                if not re.match(pattern, value):
                    error_msg = f"Ошибка в поле '{field_name}': '{value}'"
                    errors.append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
        
            # Если есть ошибки валидации
            if errors:
                logger.error(f"❌ Найдено {len(errors)} ошибок валидации")
                for error in errors:
                    bot.reply_to(message, error)
                return
        
            logger.info("✅ Валидация успешно пройдена")
        
            # Подготавливаем данные для записи
            try:
                date, account, project, direction, stage, category, description, amount, supplier, company = tuple(parts)
            
                # Определяем лист для записи
                logger.info(f"📋 Определяем лист для чата {message.chat.id}")
                worksheet = get_worksheet_for_chat(message.chat.id)
                worksheet_name = worksheet.title
                logger.info(f"📄 Выбран лист: '{worksheet_name}'")
            
                # Формируем строку для записи
                telegram_link = f"https://t.me/c/{str(message.chat.id).lstrip('-').lstrip('100')}/{message.message_id}"
                row = [
                    date,
                    account.strip(),
                    project.strip(),
                    '',
                    direction.strip().title(),
                    stage.strip(),
                    category.strip(),
                    description.strip(),
                    amount,
                    supplier.strip(),
                    telegram_link,
                    company.strip()
                ]

                logger.info(f"📝 Подготовлена строка для записи: {row}")
            
                # Находим пустую строку
                empty_row = find_empty_row(worksheet)
                logger.info(f"🔍 Найдена пустая строка: {empty_row}")
            
                if empty_row is None or empty_row > worksheet.row_count:
                    error_msg = "Не найдена подходящая строка для записи данных"
                    logger.error(f"❌ {error_msg}")
                    bot.reply_to(message, f"Ошибка: {error_msg}")
                    return
            
                # Записываем данные
                logger.info(f"💾 Начинаем запись в строку {empty_row}")
            
                for i, value in enumerate(row):
                    try:
                        worksheet.update_cell(empty_row, i + 1, value)
                        logger.debug(f"✏️ Записано в ячейку [{empty_row}, {i + 1}]: {value}")
                    except Exception as cell_error:
                        error_msg = f"Ошибка записи в ячейку [{empty_row}, {i + 1}]: {str(cell_error)}"
                        logger.error(f"❌ {error_msg}")
                        bot.reply_to(message, f"Ошибка записи: {error_msg}")
                        return
            
                # Успешная запись
                success_msg = "✅ Данные успешно добавлены в реестр оплат!"
                logger.info(f"🎉 Данные записаны в лист '{worksheet_name}', строка {empty_row}")
                bot.reply_to(message, success_msg)
            
                # Логируем статистику
                logger.info(f"📊 Обработка завершена успешно. Сумма: {amount}, Поставщик: {supplier}")
            
            except Exception as processing_error:
                error_msg = f"Ошибка обработки данных: {str(processing_error)}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                bot.reply_to(message, f"Ошибка: {error_msg}")
                return

    except IndexError as e:
        error_msg = f"Недостаточно полей в сообщении: {str(e)}"
        logger.error(f"❌ {error_msg}")
        bot.reply_to(message, "❌ Ошибка: Недостаточно полей для заполнения. Проверьте формат сообщения.")
        
    except Exception as e:
        error_msg = f"Неожиданная ошибка при обработке сообщения: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"🔍 Полный traceback: {traceback.format_exc()}")
        logger.error(f"📝 Исходное сообщение: {message.text if hasattr(message, 'text') else 'Не текстовое сообщение'}")
        bot.reply_to(message, f"❌ Произошла неожиданная ошибка: {str(e)}")
        
    finally:
        logger.info("🏁 Обработка сообщения завершена")

# --- Запуск бота ---
if __name__ == '__main__':
    logger.info("🚀 Запуск PayCollect Bot...")
    logger.info(f"🔧 Конфигурация:")
    logger.info(f"   📊 Spreadsheet ID: {SPREADSHEET_ID}")
    logger.info(f"   📄 Admin лист: {SHEET_ADMIN_NAME}")
    logger.info(f"   📄 Snab лист: {SHEET_SNAB_NAME}")
    logger.info(f"   👥 Admin чаты: {len(CHAT_ADMIN_ID.split(',')) if CHAT_ADMIN_ID else 0}")
    logger.info(f"   👥 Snab чаты: {len(CHAT_SNAB_ID.split(',')) if CHAT_SNAB_ID else 0}")
    try:
        logger.info("🔄 Начинаем polling...")
        print("Бот запущен и готов к работе! Логи записываются в bot.log")
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise
