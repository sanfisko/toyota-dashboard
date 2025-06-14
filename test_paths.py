#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы путей
"""

import os
import sys
import tempfile
import shutil

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import paths

def test_paths():
    """Тестирование системы путей"""
    print("=== Тестирование системы путей ===")
    
    # Получаем информацию о путях
    path_info = paths.get_info()
    
    print("\n📁 Информация о путях:")
    for key, value in path_info.items():
        print(f"  {key}: {value}")
    
    print(f"\n🔍 Основной путь к конфигурации: {paths.config_file}")
    
    # Проверяем доступность директорий
    print("\n📂 Проверка директорий:")
    directories = [
        ('Данные', paths.data_dir),
        ('Логи', paths.log_dir),
        ('Конфигурация', paths.config_dir),
        ('Кэш', paths.cache_dir),
        ('Временная', paths.temp_dir),
    ]
    
    for name, directory in directories:
        exists = os.path.exists(directory)
        writable = os.access(directory, os.W_OK) if exists else False
        print(f"  {name}: {directory}")
        print(f"    Существует: {'✅' if exists else '❌'}")
        print(f"    Записываемая: {'✅' if writable else '❌'}")
    
    # Проверяем файл конфигурации
    print(f"\n⚙️ Проверка файла конфигурации:")
    config_file = paths.config_file
    config_dir = os.path.dirname(config_file)
    
    print(f"  Путь: {config_file}")
    print(f"  Директория: {config_dir}")
    print(f"  Файл существует: {'✅' if os.path.exists(config_file) else '❌'}")
    print(f"  Директория существует: {'✅' if os.path.exists(config_dir) else '❌'}")
    
    if os.path.exists(config_file):
        print(f"  Файл читаемый: {'✅' if os.access(config_file, os.R_OK) else '❌'}")
        print(f"  Файл записываемый: {'✅' if os.access(config_file, os.W_OK) else '❌'}")
    
    if os.path.exists(config_dir):
        print(f"  Директория записываемая: {'✅' if os.access(config_dir, os.W_OK) else '❌'}")
    
    # Тестируем логирование
    print(f"\n📝 Тест логирования:")
    log_file = paths.log_file
    log_dir = os.path.dirname(log_file)
    
    print(f"  Путь к логу: {log_file}")
    print(f"  Директория логов: {log_dir}")
    print(f"  Директория существует: {'✅' if os.path.exists(log_dir) else '❌'}")
    
    if os.path.exists(log_dir):
        print(f"  Директория записываемая: {'✅' if os.access(log_dir, os.W_OK) else '❌'}")
        
        # Пытаемся создать тестовый лог-файл
        try:
            test_log_file = os.path.join(log_dir, 'test.log')
            with open(test_log_file, 'w') as f:
                f.write('test log entry\n')
            os.remove(test_log_file)
            print(f"  ✅ Тест записи в лог-файл успешен")
        except Exception as e:
            print(f"  ❌ Ошибка записи в лог-файл: {e}")
    else:
        print(f"  ❌ Директория логов не существует")
    
    # Тестируем создание временного файла конфигурации
    print(f"\n🧪 Тест записи конфигурации:")
    try:
        # Создаем тестовую конфигурацию
        test_config = {
            'toyota': {
                'username': 'test@example.com',
                'password': 'test_password',
                'vin': 'TEST123456789',
                'region': 'europe'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 2025
            }
        }
        
        import yaml
        
        # Пытаемся записать в основной файл конфигурации
        try:
            # Создаем директорию если нужно
            os.makedirs(config_dir, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"  ✅ Успешно записан в: {config_file}")
            
            # Проверяем чтение
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            print(f"  ✅ Успешно прочитан из: {config_file}")
            
        except (OSError, PermissionError) as e:
            print(f"  ❌ Ошибка записи в основной файл: {e}")
            
            # Пытаемся записать в альтернативное место
            fallback_path = os.path.join(os.path.expanduser("~"), '.config', 'toyota-dashboard', 'config.yaml')
            try:
                os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                with open(fallback_path, 'w', encoding='utf-8') as f:
                    yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
                print(f"  ✅ Успешно записан в альтернативное место: {fallback_path}")
            except Exception as fallback_error:
                print(f"  ❌ Ошибка записи в альтернативное место: {fallback_error}")
        
    except Exception as e:
        print(f"  ❌ Общая ошибка тестирования: {e}")
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_paths()