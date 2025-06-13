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
        try:
            # Пытаемся создать тестовый файл в системной директории
            test_dir = '/var/lib/toyota-dashboard'
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except (OSError, PermissionError):
            return False
    
    def ensure_directories(self):
        """Создает все необходимые директории"""
        directories = [
            self.data_dir,
            self.log_dir,
            self.config_dir,
            self.cache_dir,
            self.temp_dir,
            os.path.join(self.data_dir, 'backups'),
            os.path.join(self.temp_dir, 'uploads'),
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except (OSError, PermissionError) as e:
                print(f"Предупреждение: Не удалось создать директорию {directory}: {e}")
    
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
        # Сначала ищем в пользовательской директории
        user_config = os.path.join(self.config_dir, 'config.yaml')
        if os.path.exists(user_config):
            return user_config
        
        # Затем в системной директории
        if self._use_system_dirs:
            system_config = os.path.join(self._system_config_dir, 'config.yaml')
            if os.path.exists(system_config):
                return system_config
        
        # Наконец, в директории приложения (только для чтения)
        app_config = os.path.join(self._app_dir, 'config.yaml')
        if os.path.exists(app_config):
            return app_config
        
        # Возвращаем путь для создания нового файла
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