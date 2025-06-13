#!/usr/bin/env python3
"""
Тест системы путей Toyota Dashboard
"""

import os
import tempfile
from paths import paths

def test_paths():
    """Тестирование системы путей"""
    print("🔍 Тестирование системы путей Toyota Dashboard")
    print("=" * 60)
    
    # Получаем информацию о путях
    info = paths.get_info()
    
    print("📁 Информация о путях:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 Тестирование создания файлов:")
    
    # Тест создания файла в директории данных
    try:
        test_data_file = os.path.join(paths.data_dir, 'test_data.txt')
        with open(test_data_file, 'w') as f:
            f.write('test data')
        print(f"  ✅ Данные: {test_data_file}")
        os.remove(test_data_file)
    except Exception as e:
        print(f"  ❌ Данные: {e}")
    
    # Тест создания файла в директории логов
    try:
        test_log_file = os.path.join(paths.log_dir, 'test_log.txt')
        with open(test_log_file, 'w') as f:
            f.write('test log')
        print(f"  ✅ Логи: {test_log_file}")
        os.remove(test_log_file)
    except Exception as e:
        print(f"  ❌ Логи: {e}")
    
    # Тест создания файла в директории конфигурации
    try:
        test_config_file = os.path.join(paths.config_dir, 'test_config.txt')
        with open(test_config_file, 'w') as f:
            f.write('test config')
        print(f"  ✅ Конфигурация: {test_config_file}")
        os.remove(test_config_file)
    except Exception as e:
        print(f"  ❌ Конфигурация: {e}")
    
    # Тест создания файла в директории кэша
    try:
        test_cache_file = os.path.join(paths.cache_dir, 'test_cache.txt')
        with open(test_cache_file, 'w') as f:
            f.write('test cache')
        print(f"  ✅ Кэш: {test_cache_file}")
        os.remove(test_cache_file)
    except Exception as e:
        print(f"  ❌ Кэш: {e}")
    
    # Тест создания временного файла
    try:
        test_temp_file = paths.get_temp_file('test_temp.txt')
        with open(test_temp_file, 'w') as f:
            f.write('test temp')
        print(f"  ✅ Временные файлы: {test_temp_file}")
        os.remove(test_temp_file)
    except Exception as e:
        print(f"  ❌ Временные файлы: {e}")
    
    print("\n🔧 Проверка переменных окружения:")
    cache_vars = ['XDG_CACHE_HOME', 'HTTPX_CACHE_DIR']
    for var in cache_vars:
        value = os.environ.get(var, 'не установлена')
        print(f"  {var}: {value}")
    
    print("\n📂 Проверка текущей рабочей директории:")
    cwd = os.getcwd()
    print(f"  Текущая директория: {cwd}")
    
    # Проверяем, можем ли мы писать в текущую директорию
    try:
        test_cwd_file = os.path.join(cwd, 'test_write.tmp')
        with open(test_cwd_file, 'w') as f:
            f.write('test')
        os.remove(test_cwd_file)
        print(f"  ✅ Запись в текущую директорию: возможна")
    except Exception as e:
        print(f"  ❌ Запись в текущую директорию: {e}")
    
    print("\n✨ Тестирование завершено!")

if __name__ == "__main__":
    test_paths()