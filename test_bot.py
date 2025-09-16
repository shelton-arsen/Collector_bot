#!/usr/bin/env python3
"""
Тесты и проверки для PayCollect Bot
"""

import os
import re
import json
import pytest
import telebot
import gspread
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class TestBotConfiguration:
    """Тесты конфигурации бота"""
    
    def test_env_file_exists(self):
        """Проверяет наличие .env файла"""
        assert os.path.exists('.env'), "Файл .env не найден"
    
    def test_telegram_token_exists(self):
        """Проверяет наличие токена Telegram"""
        token = os.getenv('TELEGRAM_TOKEN')
        assert token is not None, "TELEGRAM_TOKEN не установлен"
        assert len(token) > 10, "TELEGRAM_TOKEN слишком короткий"
    
    def test_telegram_token_valid(self):
        """Проверяет действительность токена Telegram"""
        token = os.getenv('TELEGRAM_TOKEN')
        if token:
            try:
                bot = telebot.TeleBot(token)
                me = bot.get_me()
                assert me.username is not None, "Токен недействителен"
            except Exception as e:
                pytest.fail(f"Ошибка проверки токена: {e}")
    
    def test_spreadsheet_id_exists(self):
        """Проверяет наличие ID Google таблицы"""
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        assert spreadsheet_id is not None, "SPREADSHEET_ID не установлен"
        assert len(spreadsheet_id) > 10, "SPREADSHEET_ID слишком короткий"
    
    def test_chat_ids_exist(self):
        """Проверяет наличие ID чатов"""
        chat_admin_id = os.getenv('CHAT_ADMIN_ID')
        chat_snab_id = os.getenv('CHAT_SNAB_ID')
        
        assert chat_admin_id is not None, "CHAT_ADMIN_ID не установлен"
        assert chat_snab_id is not None, "CHAT_SNAB_ID не установлен"
    
    def test_credentials_file_exists(self):
        """Проверяет наличие файла с ключами Google API"""
        credentials_file = 'your_credentials_file.json'
        assert os.path.exists(credentials_file), f"Файл {credentials_file} не найден"
    
    def test_credentials_file_valid(self):
        """Проверяет корректность файла с ключами"""
        credentials_file = 'your_credentials_file.json'
        if os.path.exists(credentials_file):
            try:
                with open(credentials_file, 'r') as f:
                    creds = json.load(f)
                
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                for field in required_fields:
                    assert field in creds, f"Отсутствует поле: {field}"
                
                assert creds['type'] == 'service_account', "Неверный тип учетной записи"
                
            except json.JSONDecodeError:
                pytest.fail("Некорректный JSON в файле ключей")
    
    def test_google_sheets_connection(self):
        """Проверяет подключение к Google Sheets"""
        credentials_file = 'your_credentials_file.json'
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        
        if os.path.exists(credentials_file) and spreadsheet_id:
            try:
                scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                gc = gspread.service_account(filename=credentials_file, scopes=scope)
                sh = gc.open_by_key(spreadsheet_id)
                assert sh.title is not None, "Не удалось получить название таблицы"
                
            except Exception as e:
                pytest.fail(f"Ошибка подключения к Google Sheets: {e}")

class TestMessageParsing:
    """Тесты парсинга сообщений"""
    
    def test_valid_message_format(self):
        """Проверяет корректный формат сообщения"""
        test_message = "@paycollect_bot 01.01.2025 - Объект2 - Стройка МСК - Этап 3 - Оплата за окна - Оплата за окна алюминий - 30500 - ООО Петрович - ООО Дом Газобетон"
        
        # Убираем префикс и разбиваем на части
        text = test_message.lstrip('@paycollect_bot').strip()
        parts = [item.strip() for item in text.split('-')]
        
        assert len(parts) == 9, f"Ожидается 9 частей, получено {len(parts)}"
        
        # Проверяем каждую часть
        date_pattern = r"\d{2}\.\d{2}\.\d{4}"
        assert re.match(date_pattern, parts[0]), "Неверный формат даты"
        
        amount_pattern = r"^\d+$"
        assert re.match(amount_pattern, parts[6]), "Неверный формат суммы"
    
    def test_invalid_date_format(self):
        """Проверяет обработку неверного формата даты"""
        test_message = "@paycollect_bot 1.1.2025 - Объект2 - Стройка МСК - Этап 3 - Оплата за окна - Оплата за окна алюминий - 30500 - ООО Петрович - ООО Дом Газобетон"
        
        text = test_message.lstrip('@paycollect_bot').strip()
        parts = [item.strip() for item in text.split('-')]
        
        date_pattern = r"\d{2}\.\d{2}\.\d{4}"
        assert not re.match(date_pattern, parts[0]), "Дата должна быть неверной"
    
    def test_invalid_amount_format(self):
        """Проверяет обработку неверного формата суммы"""
        test_message = "@paycollect_bot 01.01.2025 - Объект2 - Стройка МСК - Этап 3 - Оплата за окна - Оплата за окна алюминий - 30500руб - ООО Петрович - ООО Дом Газобетон"
        
        text = test_message.lstrip('@paycollect_bot').strip()
        parts = [item.strip() for item in text.split('-')]
        
        amount_pattern = r"^\d+$"
        assert not re.match(amount_pattern, parts[6]), "Сумма должна быть неверной"

def run_tests():
    """Запуск всех тестов"""
    print("🧪 Запуск тестов конфигурации...")
    print("=" * 50)
    
    # Тесты конфигурации
    config_tests = TestBotConfiguration()
    
    tests = [
        ("Проверка .env файла", config_tests.test_env_file_exists),
        ("Проверка токена Telegram", config_tests.test_telegram_token_exists),
        ("Валидация токена Telegram", config_tests.test_telegram_token_valid),
        ("Проверка ID таблицы", config_tests.test_spreadsheet_id_exists),
        ("Проверка ID чатов", config_tests.test_chat_ids_exist),
        ("Проверка файла ключей", config_tests.test_credentials_file_exists),
        ("Валидация файла ключей", config_tests.test_credentials_file_valid),
        ("Подключение к Google Sheets", config_tests.test_google_sheets_connection),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    # Тесты парсинга
    print("\n🧪 Тесты парсинга сообщений...")
    print("-" * 30)
    
    parsing_tests = TestMessageParsing()
    
    parsing_test_list = [
        ("Корректный формат сообщения", parsing_tests.test_valid_message_format),
        ("Неверный формат даты", parsing_tests.test_invalid_date_format),
        ("Неверный формат суммы", parsing_tests.test_invalid_amount_format),
    ]
    
    for test_name, test_func in parsing_test_list:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    # Итоги
    print("\n" + "=" * 50)
    print(f"📊 Результаты: {passed} пройдено, {failed} провалено")
    
    if failed > 0:
        print("❌ Есть проблемы с конфигурацией. Исправьте ошибки перед запуском бота.")
        return False
    else:
        print("✅ Все тесты пройдены! Бот готов к работе.")
        return True

def quick_config_check():
    """Быстрая проверка основной конфигурации"""
    print("🔍 Быстрая проверка конфигурации...")
    
    issues = []
    
    # Проверяем основные файлы
    if not os.path.exists('.env'):
        issues.append("Отсутствует файл .env")
    
    if not os.path.exists('your_credentials_file.json'):
        issues.append("Отсутствует файл ключей Google API")
    
    # Проверяем переменные окружения
    required_vars = ['TELEGRAM_TOKEN', 'SPREADSHEET_ID', 'CHAT_ADMIN_ID', 'CHAT_SNAB_ID']
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Не установлена переменная {var}")
    
    if issues:
        print("❌ Найдены проблемы:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Основная конфигурация в порядке")
        return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_config_check()
    else:
        run_tests()
