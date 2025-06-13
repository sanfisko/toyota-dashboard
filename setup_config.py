#!/usr/bin/env python3
"""
Утилита для настройки конфигурации Toyota Dashboard
"""

import os
import shutil
from paths import paths

def setup_config():
    """Создать файл конфигурации в правильном месте."""
    
    print("🚗 Настройка конфигурации Toyota Dashboard")
    print("=" * 50)
    
    # Показать информацию о путях
    path_info = paths.get_info()
    print(f"Информация о путях:")
    print(f"  Директория приложения: {path_info['app_dir']}")
    print(f"  Директория данных: {path_info['data_dir']}")
    print(f"  Директория конфигурации: {path_info['config_dir']}")
    print(f"  Файл конфигурации: {path_info['config_file']}")
    print(f"  Использовать системные директории: {path_info['use_system_dirs']}")
    print(f"  Пользователь: {path_info['user']}")
    print()
    
    # Проверить, существует ли уже конфигурация
    if os.path.exists(paths.config_file):
        print(f"✅ Файл конфигурации уже существует: {paths.config_file}")
        return paths.config_file
    
    # Найти файл-пример
    example_config = os.path.join(paths.app_dir, 'config.example.yaml')
    if not os.path.exists(example_config):
        print(f"❌ Файл-пример конфигурации не найден: {example_config}")
        return None
    
    # Создать директорию конфигурации, если она не существует
    config_dir = os.path.dirname(paths.config_file)
    try:
        os.makedirs(config_dir, exist_ok=True)
        print(f"📁 Создана директория конфигурации: {config_dir}")
    except (OSError, PermissionError) as e:
        print(f"⚠️  Предупреждение: Не удалось создать директорию {config_dir}: {e}")
        # Попробуем использовать директорию приложения
        fallback_config = os.path.join(paths.app_dir, 'config.yaml')
        print(f"🔄 Используем альтернативный путь: {fallback_config}")
        paths.config_file = fallback_config
    
    # Скопировать файл-пример
    try:
        shutil.copy2(example_config, paths.config_file)
        print(f"✅ Файл конфигурации создан: {paths.config_file}")
        print()
        print("📝 Теперь отредактируйте файл конфигурации:")
        print(f"   nano {paths.config_file}")
        print()
        print("🔧 Обязательно измените следующие параметры:")
        print("   toyota:")
        print("     username: \"ваш-email@example.com\"")
        print("     password: \"ваш-пароль\"")
        print("     vin: \"ВАШ_VIN_НОМЕР\"")
        print()
        return paths.config_file
    except (OSError, PermissionError) as e:
        print(f"❌ Не удалось создать файл конфигурации: {e}")
        return None

if __name__ == "__main__":
    setup_config()