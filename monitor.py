#!/usr/bin/env python3
"""
Веб-интерфейс для мониторинга и управления Telegram ботом
"""

import os
import sys
import json
import time
import psutil
import subprocess
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv
import telebot
import gspread

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)

class BotMonitor:
    def __init__(self):
        self.bot_process = None
        self.bot_pid = None
        self.start_time = None
        self.stats = {
            'messages_processed': 0,
            'errors': 0,
            'uptime': 0,
            'last_activity': None
        }
        self.logs = []
        self.max_logs = 1000
        
    def log(self, level, message):
        """Добавляет запись в лог"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        print(f"[{timestamp}] {level}: {message}")
    
    def start_bot(self):
        """Запускает бота"""
        if self.is_bot_running():
            self.log('WARNING', 'Бот уже запущен')
            return False
            
        try:
            # Запускаем бота в отдельном процессе
            cmd = [sys.executable, 'bot.py']
            self.bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.bot_pid = self.bot_process.pid
            self.start_time = datetime.now()
            self.log('INFO', f'Бот запущен с PID: {self.bot_pid}')
            
            # Запускаем мониторинг вывода бота
            threading.Thread(target=self._monitor_bot_output, daemon=True).start()
            return True
            
        except Exception as e:
            self.log('ERROR', f'Ошибка запуска бота: {e}')
            return False
    
    def stop_bot(self):
        """Останавливает бота"""
        if not self.is_bot_running():
            self.log('WARNING', 'Бот не запущен')
            return False
            
        try:
            if self.bot_process:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
            self.log('INFO', 'Бот остановлен')
            self.bot_process = None
            self.bot_pid = None
            self.start_time = None
            return True
            
        except Exception as e:
            self.log('ERROR', f'Ошибка остановки бота: {e}')
            return False
    
    def restart_bot(self):
        """Перезапускает бота"""
        self.log('INFO', 'Перезапуск бота...')
        self.stop_bot()
        time.sleep(2)
        return self.start_bot()
    
    def is_bot_running(self):
        """Проверяет, запущен ли бот"""
        if self.bot_process is None:
            return False
        
        # Проверяем статус процесса
        try:
            return self.bot_process.poll() is None
        except:
            return False
    
    def get_bot_status(self):
        """Возвращает статус бота"""
        status = {
            'running': self.is_bot_running(),
            'pid': self.bot_pid,
            'uptime': self._get_uptime(),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage()
        }
        return status
    
    def _get_uptime(self):
        """Возвращает время работы бота"""
        if self.start_time is None:
            return 0
        return int((datetime.now() - self.start_time).total_seconds())
    
    def _get_memory_usage(self):
        """Возвращает использование памяти ботом"""
        if not self.bot_pid:
            return 0
        try:
            process = psutil.Process(self.bot_pid)
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0
    
    def _get_cpu_usage(self):
        """Возвращает использование CPU ботом"""
        if not self.bot_pid:
            return 0
        try:
            process = psutil.Process(self.bot_pid)
            return process.cpu_percent()
        except:
            return 0
    
    def _monitor_bot_output(self):
        """Мониторит вывод бота"""
        if not self.bot_process:
            return
            
        try:
            while self.bot_process.poll() is None:
                output = self.bot_process.stdout.readline()
                if output:
                    self.log('BOT_OUTPUT', output.strip())
                error = self.bot_process.stderr.readline()
                if error:
                    self.log('BOT_ERROR', error.strip())
                    self.stats['errors'] += 1
        except Exception as e:
            self.log('ERROR', f'Ошибка мониторинга вывода: {e}')

class ConfigChecker:
    def __init__(self):
        self.checks = []
    
    def check_all(self):
        """Выполняет все проверки конфигурации"""
        self.checks = []
        
        # Проверка .env файла
        self._check_env_file()
        
        # Проверка токена бота
        self._check_telegram_token()
        
        # Проверка Google Sheets
        self._check_google_sheets()
        
        # Проверка JSON файла с ключами
        self._check_credentials_file()
        
        return self.checks
    
    def _check_env_file(self):
        """Проверяет .env файл"""
        if not os.path.exists('.env'):
            self.checks.append({
                'name': '.env файл',
                'status': 'error',
                'message': 'Файл .env не найден'
            })
            return
        
        required_vars = ['TELEGRAM_TOKEN', 'SPREADSHEET_ID', 'CHAT_ADMIN_ID', 'CHAT_SNAB_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.checks.append({
                'name': '.env файл',
                'status': 'error',
                'message': f'Отсутствуют переменные: {", ".join(missing_vars)}'
            })
        else:
            self.checks.append({
                'name': '.env файл',
                'status': 'success',
                'message': 'Все переменные окружения настроены'
            })
    
    def _check_telegram_token(self):
        """Проверяет токен Telegram бота"""
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            self.checks.append({
                'name': 'Telegram токен',
                'status': 'error',
                'message': 'Токен не установлен'
            })
            return
        
        try:
            bot = telebot.TeleBot(token)
            me = bot.get_me()
            self.checks.append({
                'name': 'Telegram токен',
                'status': 'success',
                'message': f'Токен действителен. Бот: @{me.username}'
            })
        except Exception as e:
            self.checks.append({
                'name': 'Telegram токен',
                'status': 'error',
                'message': f'Ошибка проверки токена: {str(e)}'
            })
    
    def _check_google_sheets(self):
        """Проверяет подключение к Google Sheets"""
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id:
            self.checks.append({
                'name': 'Google Sheets',
                'status': 'error',
                'message': 'ID таблицы не установлен'
            })
            return
        
        try:
            credentials_file = 'your_credentials_file.json'
            if not os.path.exists(credentials_file):
                self.checks.append({
                    'name': 'Google Sheets',
                    'status': 'error',
                    'message': f'Файл ключей {credentials_file} не найден'
                })
                return
            
            gc = gspread.service_account(filename=credentials_file)
            sh = gc.open_by_key(spreadsheet_id)
            
            self.checks.append({
                'name': 'Google Sheets',
                'status': 'success',
                'message': f'Подключение успешно. Таблица: {sh.title}'
            })
            
        except Exception as e:
            self.checks.append({
                'name': 'Google Sheets',
                'status': 'error',
                'message': f'Ошибка подключения: {str(e)}'
            })
    
    def _check_credentials_file(self):
        """Проверяет файл с ключами Google API"""
        credentials_file = 'your_credentials_file.json'
        
        if not os.path.exists(credentials_file):
            self.checks.append({
                'name': 'Файл ключей',
                'status': 'error',
                'message': f'Файл {credentials_file} не найден'
            })
            return
        
        try:
            with open(credentials_file, 'r') as f:
                creds = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                self.checks.append({
                    'name': 'Файл ключей',
                    'status': 'error',
                    'message': f'Отсутствуют поля: {", ".join(missing_fields)}'
                })
            else:
                self.checks.append({
                    'name': 'Файл ключей',
                    'status': 'success',
                    'message': f'Файл корректен. Проект: {creds.get("project_id")}'
                })
                
        except Exception as e:
            self.checks.append({
                'name': 'Файл ключей',
                'status': 'error',
                'message': f'Ошибка чтения файла: {str(e)}'
            })

# Инициализация
monitor = BotMonitor()
config_checker = ConfigChecker()

# Веб-маршруты
@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API для получения статуса бота"""
    status = monitor.get_bot_status()
    system_info = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }
    return jsonify({
        'bot': status,
        'system': system_info,
        'stats': monitor.stats
    })

@app.route('/api/logs')
def api_logs():
    """API для получения логов"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(monitor.logs[-limit:])

@app.route('/api/config/check')
def api_config_check():
    """API для проверки конфигурации"""
    checks = config_checker.check_all()
    return jsonify(checks)

@app.route('/api/bot/start', methods=['POST'])
def api_bot_start():
    """API для запуска бота"""
    success = monitor.start_bot()
    return jsonify({'success': success})

@app.route('/api/bot/stop', methods=['POST'])
def api_bot_stop():
    """API для остановки бота"""
    success = monitor.stop_bot()
    return jsonify({'success': success})

@app.route('/api/bot/restart', methods=['POST'])
def api_bot_restart():
    """API для перезапуска бота"""
    success = monitor.restart_bot()
    return jsonify({'success': success})

@app.route('/api/test/message', methods=['POST'])
def api_test_message():
    """API для отправки тестового сообщения"""
    try:
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('CHAT_ADMIN_ID', '').split(',')[0].strip()
        
        if not token or not chat_id:
            return jsonify({'success': False, 'error': 'Токен или Chat ID не настроены'})
        
        bot = telebot.TeleBot(token)
        test_message = "@paycollect_bot 01.01.2025 - Тест - Тестовый регион - Тестовый этап - Тестовая категория - Тестовое описание - 1000 - Тестовый поставщик - Тестовая компания"
        
        bot.send_message(chat_id, f"🧪 Тестовое сообщение:\n{test_message}")
        
        return jsonify({'success': True, 'message': 'Тестовое сообщение отправлено'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Создаем директорию для шаблонов, если её нет
    os.makedirs('templates', exist_ok=True)
    
    # Логирование запуска
    monitor.log('INFO', 'Система мониторинга запущена')
    
    # Запускаем веб-сервер
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('MONITOR_PORT', 5000)),
        debug=False
    )
