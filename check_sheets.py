#!/usr/bin/env python3
"""
Скрипт для проверки доступных листов в Google таблице
"""

import os
import gspread
from dotenv import load_dotenv

load_dotenv()

def check_available_sheets():
    """Проверяет доступные листы в таблице"""
    try:
        # Параметры подключения
        SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        CREDENTIALS_FILE = 'your_credentials_file.json'
        
        print(f"📊 Подключение к таблице: {SPREADSHEET_ID}")
        print(f"🔑 Файл ключей: {CREDENTIALS_FILE}")
        
        # Подключение к Google Sheets
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        gc = gspread.service_account(filename=CREDENTIALS_FILE, scopes=scope)
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        print(f"✅ Успешно подключились к таблице: '{sh.title}'")
        print(f"📋 Доступные листы:")
        
        for i, worksheet in enumerate(sh.worksheets(), 1):
            print(f"   {i}. '{worksheet.title}' (ID: {worksheet.id})")
        
        print(f"\n🔧 Текущие настройки в .env:")
        print(f"   SHEET_ADMIN_NAME = {os.getenv('SHEET_ADMIN_NAME', 'не установлено')}")
        print(f"   SHEET_SNAB_NAME = {os.getenv('SHEET_SNAB_NAME', 'не установлено')}")
        
        # Проверяем, какие листы существуют
        admin_sheet = os.getenv('SHEET_ADMIN_NAME')
        snab_sheet = os.getenv('SHEET_SNAB_NAME')
        
        if admin_sheet:
            try:
                sh.worksheet(admin_sheet)
                print(f"✅ Лист '{admin_sheet}' найден")
            except gspread.exceptions.WorksheetNotFound:
                print(f"❌ Лист '{admin_sheet}' не найден")
        
        if snab_sheet:
            try:
                sh.worksheet(snab_sheet)
                print(f"✅ Лист '{snab_sheet}' найден")
            except gspread.exceptions.WorksheetNotFound:
                print(f"❌ Лист '{snab_sheet}' не найден")
                
        return sh.worksheets()
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

if __name__ == '__main__':
    check_available_sheets()
