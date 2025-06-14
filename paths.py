#!/usr/bin/env python3
"""
Модуль управления путями для Toyota Dashboard
Обеспечивает правильное размещение всех файлов в системных директориях
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

class PathManager:
    """Менеджер путей для Toyota Dashboard"""
    
    def __init__(self):
        self._app_dir = os.path.dirname(os.path.abspath(__file__))
        self._user_home = os.path.expanduser("~")
        self._setup_paths()
    
    def _setup_paths(self):
        """Настройка всех путей приложения"""
        # Определяем пользователя
        self._user = os.getenv('USER', 'toyota')
        
        # Базовые системные директории
        self._system_data_dir = '/var/lib/toyota-dashboard'
        self._system_log_dir = '/var/log/toyota-dashboard'
        self._system_config_dir = '/etc/toyota-dashboard'
        
        # Пользовательские директории
        self._user_config_dir = os.path.join(self._user_home, '.config', 'toyota-dashboard')
        self._user_cache_dir = os.path.join(self._user_home, '.cache', 'toyota-dashboard')
        self._user_data_dir = os.path.join(self._user_home, '.local', 'share', 'toyota-dashboard')
        
        # Временные директории
        self._temp_dir = os.path.join(tempfile.gettempdir(), 'toyota-dashboard')
        
        # Определяем, какие директории использовать
        self._use_system_dirs = self._can_use_system_dirs()
        
    def _can_use_system_dirs(self) -> bool:
        """Проверяет, можно ли использовать системные директории"""
        # Принудительно используем пользовательские директории для безопасности
        # и избежания проблем с правами доступа
        return False
    
    def ensure_directories(self):
        """Создает все необходимые директории"""
        directories = [
            ('Данные', self.data_dir),
            ('Логи', self.log_dir),
            ('Конфигурация', self.config_dir),
            ('Кэш', self.cache_dir),
            ('Временная', self.temp_dir),
            ('Резервные копии', os.path.join(self.data_dir, 'backups')),
            ('Загрузки', os.path.join(self.temp_dir, 'uploads')),
        ]
        
        created_count = 0
        failed_count = 0
        
        for name, directory in directories:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    print(f"✅ Создана директория {name}: {directory}")
                    created_count += 1
                else:
                    # Проверяем права на запись
                    if os.access(directory, os.W_OK):
                        print(f"✅ Директория {name} доступна: {directory}")
                    else:
                        print(f"⚠️ Директория {name} недоступна для записи: {directory}")
                        failed_count += 1
                        
            except (OSError, PermissionError) as e:
                print(f"❌ Не удалось создать директорию {name} ({directory}): {e}")
                failed_count += 1
        
        if created_count > 0:
            print(f"📁 Создано директорий: {created_count}")
        if failed_count > 0:
            print(f"⚠️ Проблем с директориями: {failed_count}")
            print("💡 Рекомендация: Проверьте права доступа или используйте пользовательские директории")
    
    @property
    def app_dir(self) -> str:
        """Директория приложения (только для чтения)"""
        return self._app_dir
    
    @property
    def data_dir(self) -> str:
        """Директория для данных"""
        if self._use_system_dirs:
            return os.path.join(self._system_data_dir, 'data')
        return self._user_data_dir
    
    @property
    def log_dir(self) -> str:
        """Директория для логов"""
        if self._use_system_dirs:
            return self._system_log_dir
        return os.path.join(self._user_data_dir, 'logs')
    
    @property
    def config_dir(self) -> str:
        """Директория для конфигурации"""
        if self._use_system_dirs:
            return self._system_config_dir
        return self._user_config_dir
    
    @property
    def cache_dir(self) -> str:
        """Директория для кэша"""
        return self._user_cache_dir
    
    @property
    def temp_dir(self) -> str:
        """Временная директория"""
        return self._temp_dir
    
    @property
    def database_path(self) -> str:
        """Путь к файлу базы данных"""
        return os.path.join(self.data_dir, 'toyota.db')
    
    @property
    def config_file(self) -> str:
        """Путь к файлу конфигурации"""
        # Определяем возможные пути к конфигурации в порядке приоритета
        user_config = os.path.join(self.config_dir, 'config.yaml')
        system_config = os.path.join(self._system_config_dir, 'config.yaml')
        app_config = os.path.join(self._app_dir, 'config.yaml')
        
        # 1. Если файл уже существует в пользовательской директории, используем его
        if os.path.exists(user_config):
            return user_config
        
        # 2. Если используем системные директории и файл существует там
        if self._use_system_dirs and os.path.exists(system_config):
            # Дополнительно проверяем права на запись в системную конфигурацию
            try:
                with open(system_config, 'a'):
                    pass
                return system_config
            except (OSError, PermissionError):
                # Если нет прав на запись в системную конфигурацию,
                # копируем её в пользовательскую директорию
                try:
                    import shutil
                    os.makedirs(self.config_dir, exist_ok=True)
                    shutil.copy2(system_config, user_config)
                    return user_config
                except (OSError, PermissionError):
                    pass
        
        # 3. Проверяем файл в директории приложения (только для чтения)
        if os.path.exists(app_config):
            # Копируем его в пользовательскую директорию для возможности редактирования
            try:
                import shutil
                os.makedirs(self.config_dir, exist_ok=True)
                shutil.copy2(app_config, user_config)
                return user_config
            except (OSError, PermissionError):
                pass
        
        # 4. Если используем системные директории и можем писать туда
        if self._use_system_dirs:
            try:
                # Проверяем возможность создания файла в системной директории
                os.makedirs(self._system_config_dir, exist_ok=True)
                test_file = os.path.join(self._system_config_dir, '.test_config_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return system_config
            except (OSError, PermissionError):
                pass
        
        # 5. Возвращаем путь для создания нового файла в пользовательской директории
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except (OSError, PermissionError):
            pass
        return user_config
    
    @property
    def log_file(self) -> str:
        """Путь к файлу логов"""
        return os.path.join(self.log_dir, 'app.log')
    
    def get_static_file(self, filename: str) -> str:
        """Получить путь к статическому файлу"""
        return os.path.join(self._app_dir, 'static', filename)
    
    def get_backup_path(self, filename: str) -> str:
        """Получить путь для резервной копии"""
        return os.path.join(self.data_dir, 'backups', filename)
    
    def get_temp_file(self, filename: str) -> str:
        """Получить путь к временному файлу"""
        return os.path.join(self.temp_dir, filename)
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Очистка старых временных файлов"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if current_time - os.path.getmtime(file_path) > max_age_seconds:
                            os.remove(file_path)
                    except (OSError, PermissionError):
                        pass
        except Exception:
            pass
    
    def get_info(self) -> dict:
        """Получить информацию о путях"""
        return {
            'app_dir': self.app_dir,
            'data_dir': self.data_dir,
            'log_dir': self.log_dir,
            'config_dir': self.config_dir,
            'cache_dir': self.cache_dir,
            'temp_dir': self.temp_dir,
            'database_path': self.database_path,
            'config_file': self.config_file,
            'log_file': self.log_file,
            'use_system_dirs': self._use_system_dirs,
            'user': self._user,
        }

# Глобальный экземпляр менеджера путей
paths = PathManager()

# Создаем все необходимые директории при импорте
paths.ensure_directories()