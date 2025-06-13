#!/usr/bin/env python3
"""
Утилита для проверки путей Toyota Dashboard
"""

import os
from paths import paths

def check_paths():
    """Проверить все пути и показать информацию."""
    
    print("🚗 Проверка путей Toyota Dashboard")
    print("=" * 50)
    
    path_info = paths.get_info()
    
    print(f"Пользователь: {path_info['user']}")
    print(f"Использовать системные директории: {path_info['use_system_dirs']}")
    print()
    
    # Проверить каждый путь
    paths_to_check = [
        ("Директория приложения", path_info['app_dir']),
        ("Директория данных", path_info['data_dir']),
        ("Директория логов", path_info['log_dir']),
        ("Директория конфигурации", path_info['config_dir']),
        ("Директория кэша", path_info['cache_dir']),
        ("Временная директория", path_info['temp_dir']),
        ("Файл базы данных", path_info['database_path']),
        ("Файл конфигурации", path_info['config_file']),
        ("Файл логов", path_info['log_file']),
    ]
    
    for name, path in paths_to_check:
        exists = os.path.exists(path)
        writable = False
        
        if exists:
            try:
                # Проверить возможность записи
                if os.path.isdir(path):
                    test_file = os.path.join(path, '.test_write')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    writable = True
                else:
                    # Для файлов проверяем директорию
                    dir_path = os.path.dirname(path)
                    if os.path.exists(dir_path):
                        test_file = os.path.join(dir_path, '.test_write')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        writable = True
            except (OSError, PermissionError):
                writable = False
        
        status = "✅" if exists else "❌"
        write_status = "✍️" if writable else "🔒"
        
        print(f"{status} {write_status} {name}: {path}")
    
    print()
    print("Легенда:")
    print("✅ - существует, ❌ - не существует")
    print("✍️ - доступен для записи, 🔒 - только для чтения")

if __name__ == "__main__":
    check_paths()