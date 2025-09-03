#!/usr/bin/env python3
"""
Скрипт управления ботом и системой мониторинга
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path

class BotManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.venv_python = self.base_dir / '.venv' / 'bin' / 'python'
        self.bot_script = self.base_dir / 'bot.py'
        self.monitor_script = self.base_dir / 'monitor.py'
        
        # Файлы для хранения PID
        self.bot_pid_file = self.base_dir / '.bot.pid'
        self.monitor_pid_file = self.base_dir / '.monitor.pid'
    
    def start_bot(self):
        """Запуск бота"""
        if self.is_bot_running():
            print("❌ Бот уже запущен")
            return False
        
        print("🚀 Запуск бота...")
        try:
            process = subprocess.Popen(
                [str(self.venv_python), str(self.bot_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            
            # Сохраняем PID
            with open(self.bot_pid_file, 'w') as f:
                f.write(str(process.pid))
            
            print(f"✅ Бот запущен с PID: {process.pid}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def stop_bot(self):
        """Остановка бота"""
        if not self.is_bot_running():
            print("❌ Бот не запущен")
            return False
        
        pid = self.get_bot_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                
                # Проверяем, что процесс завершился
                try:
                    os.kill(pid, 0)
                    # Если процесс все еще работает, принудительно завершаем
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
                
                # Удаляем PID файл
                if self.bot_pid_file.exists():
                    self.bot_pid_file.unlink()
                
                print("✅ Бот остановлен")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка остановки бота: {e}")
                return False
    
    def restart_bot(self):
        """Перезапуск бота"""
        print("🔄 Перезапуск бота...")
        self.stop_bot()
        time.sleep(2)
        return self.start_bot()
    
    def start_monitor(self):
        """Запуск системы мониторинга"""
        if self.is_monitor_running():
            print("❌ Мониторинг уже запущен")
            return False
        
        print("🚀 Запуск системы мониторинга...")
        try:
            process = subprocess.Popen(
                [str(self.venv_python), str(self.monitor_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            
            # Сохраняем PID
            with open(self.monitor_pid_file, 'w') as f:
                f.write(str(process.pid))
            
            port = os.getenv('MONITOR_PORT', 5000)
            print(f"✅ Мониторинг запущен с PID: {process.pid}")
            print(f"🌐 Веб-интерфейс: http://212.109.192.79:{port}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска мониторинга: {e}")
            return False
    
    def stop_monitor(self):
        """Остановка системы мониторинга"""
        if not self.is_monitor_running():
            print("❌ Мониторинг не запущен")
            return False
        
        pid = self.get_monitor_pid()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                
                # Проверяем, что процесс завершился
                try:
                    os.kill(pid, 0)
                    # Если процесс все еще работает, принудительно завершаем
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
                
                # Удаляем PID файл
                if self.monitor_pid_file.exists():
                    self.monitor_pid_file.unlink()
                
                print("✅ Мониторинг остановлен")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка остановки мониторинга: {e}")
                return False
    
    def status(self):
        """Показывает статус всех компонентов"""
        print("📊 Статус системы:")
        print("-" * 40)
        
        # Статус бота
        if self.is_bot_running():
            pid = self.get_bot_pid()
            print(f"🤖 Бот: ✅ Работает (PID: {pid})")
        else:
            print("🤖 Бот: ❌ Остановлен")
        
        # Статус мониторинга
        if self.is_monitor_running():
            pid = self.get_monitor_pid()
            port = os.getenv('MONITOR_PORT', 5000)
            print(f"📊 Мониторинг: ✅ Работает (PID: {pid})")
            print(f"🌐 Веб-интерфейс: http://localhost:{port}")
        else:
            print("📊 Мониторинг: ❌ Остановлен")
        
        print("-" * 40)
    
    def start_all(self):
        """Запуск всех компонентов"""
        print("🚀 Запуск всех компонентов...")
        self.start_bot()
        time.sleep(2)
        self.start_monitor()
    
    def stop_all(self):
        """Остановка всех компонентов"""
        print("⏹️ Остановка всех компонентов...")
        self.stop_bot()
        self.stop_monitor()
    
    def restart_all(self):
        """Перезапуск всех компонентов"""
        print("🔄 Перезапуск всех компонентов...")
        self.stop_all()
        time.sleep(3)
        self.start_all()
    
    def is_bot_running(self):
        """Проверяет, запущен ли бот"""
        pid = self.get_bot_pid()
        if pid is None:
            return False
        
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # Процесс не существует, удаляем PID файл
            if self.bot_pid_file.exists():
                self.bot_pid_file.unlink()
            return False
    
    def is_monitor_running(self):
        """Проверяет, запущен ли мониторинг"""
        pid = self.get_monitor_pid()
        if pid is None:
            return False
        
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # Процесс не существует, удаляем PID файл
            if self.monitor_pid_file.exists():
                self.monitor_pid_file.unlink()
            return False
    
    def get_bot_pid(self):
        """Получает PID бота"""
        if not self.bot_pid_file.exists():
            return None
        
        try:
            with open(self.bot_pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    
    def get_monitor_pid(self):
        """Получает PID мониторинга"""
        if not self.monitor_pid_file.exists():
            return None
        
        try:
            with open(self.monitor_pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None
    
    def install_service(self):
        """Создает systemd service для автозапуска"""
        service_content = f"""[Unit]
Description=PayCollect Bot Service
After=network.target

[Service]
Type=forking
User=www-root
WorkingDirectory={self.base_dir}
ExecStart={self.base_dir}/manage.py start-all
ExecStop={self.base_dir}/manage.py stop-all
ExecReload={self.base_dir}/manage.py restart-all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = '/etc/systemd/system/paycollect-bot.service'
        
        try:
            print("📝 Создание systemd service...")
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Делаем скрипт исполняемым
            os.chmod(__file__, 0o755)
            
            # Перезагружаем systemd и включаем сервис
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'paycollect-bot'], check=True)
            
            print("✅ Systemd service создан и включен")
            print("🔧 Управление сервисом:")
            print("   systemctl start paycollect-bot")
            print("   systemctl stop paycollect-bot")
            print("   systemctl status paycollect-bot")
            
        except PermissionError:
            print("❌ Нужны права sudo для создания systemd service")
            print("💡 Запустите: sudo python3 manage.py install-service")
        except Exception as e:
            print(f"❌ Ошибка создания service: {e}")

def main():
    parser = argparse.ArgumentParser(description='Управление PayCollect Bot')
    
    parser.add_argument('command', choices=[
        'start-bot', 'stop-bot', 'restart-bot',
        'start-monitor', 'stop-monitor',
        'start-all', 'stop-all', 'restart-all',
        'status', 'install-service'
    ], help='Команда для выполнения')
    
    args = parser.parse_args()
    manager = BotManager()
    
    commands = {
        'start-bot': manager.start_bot,
        'stop-bot': manager.stop_bot,
        'restart-bot': manager.restart_bot,
        'start-monitor': manager.start_monitor,
        'stop-monitor': manager.stop_monitor,
        'start-all': manager.start_all,
        'stop-all': manager.stop_all,
        'restart-all': manager.restart_all,
        'status': manager.status,
        'install-service': manager.install_service
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            command_func()
        except KeyboardInterrupt:
            print("\n⏹️ Операция прервана пользователем")
            sys.exit(1)
    else:
        print(f"❌ Неизвестная команда: {args.command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
