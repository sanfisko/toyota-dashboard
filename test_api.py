#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API endpoints
"""

import asyncio
import json
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api():
    """Тестирование API endpoints"""
    print("=== Тестирование API endpoints ===")
    
    try:
        # Импортируем FastAPI приложение
        from app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тестируем endpoint диагностики путей
        print("\n🔍 Тестирование /api/system/paths")
        response = client.get("/api/system/paths")
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешно получена информация о путях")
            
            # Выводим основную информацию
            if 'paths' in data:
                print("\n📁 Основные пути:")
                for key, value in data['paths'].items():
                    print(f"  {key}: {value}")
            
            if 'config_file_status' in data:
                config_status = data['config_file_status']
                print(f"\n⚙️ Статус файла конфигурации:")
                print(f"  Путь: {config_status['path']}")
                print(f"  Существует: {'✅' if config_status['exists'] else '❌'}")
                print(f"  Читаемый: {'✅' if config_status['readable'] else '❌'}")
                print(f"  Записываемый: {'✅' if config_status['writable'] else '❌'}")
            
            if 'alternative_paths' in data:
                print(f"\n📂 Альтернативные пути:")
                for alt in data['alternative_paths']:
                    print(f"  {alt['path']}")
                    print(f"    Файл: {'✅' if alt['exists'] else '❌'}")
                    print(f"    Директория: {'✅' if alt['dir_exists'] else '❌'}")
                    print(f"    Записываемая: {'✅' if alt['dir_writable'] else '❌'}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
        
        # Тестируем сохранение конфигурации
        print(f"\n💾 Тестирование сохранения конфигурации")
        test_config = {
            "username": "test@example.com",
            "password": "test_password",
            "vin": "TEST123456789",
            "region": "europe",
            "port": 2025
        }
        
        response = client.post("/api/save-config", json=test_config)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Конфигурация успешно сохранена")
                if 'config_path' in result:
                    print(f"  Путь: {result['config_path']}")
            else:
                print(f"❌ Ошибка сохранения: {result.get('error', 'Неизвестная ошибка')}")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Детали: {error_data.get('error', 'Нет деталей')}")
            except:
                print(f"  Ответ: {response.text}")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что установлены все зависимости")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
    
    print("\n=== Тестирование API завершено ===")

if __name__ == "__main__":
    # Проверяем наличие FastAPI
    try:
        import fastapi
        from fastapi.testclient import TestClient
        asyncio.run(test_api())
    except ImportError:
        print("❌ FastAPI не установлен. Устанавливаем...")
        os.system("pip install fastapi[all]")
        print("Попробуйте запустить тест снова")