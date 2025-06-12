#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы приложения
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Импортируем модули...")
    from app import app, config
    print("Модули импортированы успешно")
    
    print(f"Конфигурация загружена: {config.get('toyota', {}).get('username', 'НЕ НАСТРОЕНО')}")
    
    import uvicorn
    print("Запускаем сервер...")
    uvicorn.run(app, host="0.0.0.0", port=12000, log_level="info")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()