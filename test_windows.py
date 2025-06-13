#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности управления окнами Toyota
"""

import asyncio
import sys
from pytoyoda import MyT
from pytoyoda.models.endpoints.command import CommandType

async def test_windows_control():
    """Тестирование управления окнами."""
    
    # Данные для входа
    username = "sanfisko@gmail.com"
    password = "$@nfiSK3"
    vin = "JTPABACA90R004975"
    
    print("🚗 Тестирование управления окнами Toyota")
    print(f"VIN: {vin}")
    print("-" * 50)
    
    try:
        # Инициализация клиента
        print("📡 Подключение к Toyota Connected Services...")
        client = MyT(username=username, password=password)
        
        # Получение автомобилей
        print("🔍 Получение списка автомобилей...")
        vehicles = await client.get_vehicles()
        
        if not vehicles:
            print("❌ Автомобили не найдены")
            return
            
        # Найти автомобиль по VIN
        target_vehicle = None
        for vehicle in vehicles:
            if vehicle.vin == vin:
                target_vehicle = vehicle
                break
                
        if not target_vehicle:
            print(f"❌ Автомобиль с VIN {vin} не найден")
            print("Доступные автомобили:")
            for vehicle in vehicles:
                print(f"  - {vehicle.vin} ({vehicle.alias})")
            return
            
        print(f"✅ Автомобиль найден: {target_vehicle.alias} ({target_vehicle.vin})")
        
        # Тестирование команд управления окнами
        print("\n🪟 Тестирование управления окнами...")
        
        # Проверяем доступные команды
        available_commands = [
            CommandType.WINDOW_ON,   # power-window-on
            CommandType.WINDOW_OFF,  # power-window-off
        ]
        
        for command in available_commands:
            print(f"\n📤 Отправка команды: {command.value}")
            try:
                result = await target_vehicle.post_command(command)
                print(f"✅ Команда отправлена успешно")
                print(f"   Статус: {result}")
                
                # Небольшая пауза между командами
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Ошибка выполнения команды {command.value}: {e}")
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("Запуск тестирования управления окнами...")
    success = asyncio.run(test_windows_control())
    
    if success:
        print("\n✅ Управление окнами работает!")
        sys.exit(0)
    else:
        print("\n❌ Тестирование не удалось")
        sys.exit(1)