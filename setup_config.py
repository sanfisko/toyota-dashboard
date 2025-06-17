#!/usr/bin/env python3
"""
Скрипт настройки конфигурации Toyota Dashboard
Создает базовый config.yaml файл с пустыми значениями
"""

import os
import yaml
from pathlib import Path

def create_default_config():
    """Создает базовый конфигурационный файл"""
    
    config = {
        'toyota': {
            'username': '',
            'password': '',
            'vin': '',
            'region': 'europe'  # Зафиксировано для европейских автомобилей
        },
        'server': {
            'host': '0.0.0.0',
            'port': 2025,
            'debug': False,
            'secret_key': 'your-secret-key-here'
        },
        'dashboard': {
            'language': 'ru',
            'theme': 'auto',
            'units': 'metric',
            'currency': 'RUB',
            'fuel_price': 50.0,
            'electricity_price': 5.0
        },
        'monitoring': {
            'auto_refresh': True,
            'data_collection_interval': 300,
            'trip_detection': True
        },
        'notifications': {
            'daily_reports': False,
            'low_fuel_threshold': 50,
            'low_battery_threshold': 20
        },
        'database': {
            'path': 'data/toyota_dashboard.db'
        },
        'cache': {
            'enabled': True,
            'ttl': 300,
            'directory': '~/.cache/toyota-dashboard'
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/toyota-dashboard.log',
            'max_size': '10MB',
            'backup_count': 5
        }
    }
    
    # Создаем директории если их нет
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Записываем конфигурацию
    with open('config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print("✓ Базовый конфигурационный файл создан: config.yaml")
    print("✓ Директории созданы: data/, logs/")
    print("")
    print("📝 Следующие шаги:")
    print("1. Запустите сервис:")
    print("   sudo systemctl start toyota-dashboard")
    print("")
    print("2. Откройте в браузере:")
    print("   http://localhost:2025")
    print("")
    print("3. Настройте Toyota данные через веб-интерфейс:")
    print("   - Система автоматически перенаправит на страницу настройки")
    print("   - Введите email, пароль и VIN номер автомобиля")
    print("   - Нажмите 'Проверить и сохранить настройки'")

if __name__ == '__main__':
    create_default_config()