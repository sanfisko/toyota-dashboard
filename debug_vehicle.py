#!/usr/bin/env python3
"""
Отладочный скрипт для изучения структуры объекта Vehicle
"""

import asyncio
from pytoyoda import MyT

async def debug_vehicle():
    """Отладка структуры Vehicle."""
    
    username = "sanfisko@gmail.com"
    password = "$@nfiSK3"
    vin = "JTPABACA90R004975"
    
    try:
        client = MyT(username=username, password=password)
        vehicles = await client.get_vehicles()
        
        if not vehicles:
            print("Автомобили не найдены")
            return
            
        vehicle = vehicles[0]
        
        print("=== Структура объекта Vehicle ===")
        print(f"Тип: {type(vehicle)}")
        print(f"Атрибуты: {dir(vehicle)}")
        
        print("\n=== Приватные атрибуты ===")
        if hasattr(vehicle, '_vehicle_info'):
            print(f"_vehicle_info: {type(vehicle._vehicle_info)}")
            vehicle_info = vehicle._vehicle_info
            
            print(f"\n=== Атрибуты vehicle_info ===")
            print(f"Тип: {type(vehicle_info)}")
            
            if hasattr(vehicle_info, 'extended_capabilities'):
                print(f"\nextended_capabilities: {type(vehicle_info.extended_capabilities)}")
                ext_caps = vehicle_info.extended_capabilities
                if ext_caps:
                    print(f"power_windows_capable: {ext_caps.power_windows_capable}")
                    print(f"door_lock_unlock_capable: {ext_caps.door_lock_unlock_capable}")
                    print(f"climate_capable: {ext_caps.climate_capable}")
                else:
                    print("extended_capabilities is None")
            
            if hasattr(vehicle_info, 'remote_service_capabilities'):
                print(f"\nremote_service_capabilities: {type(vehicle_info.remote_service_capabilities)}")
                remote_caps = vehicle_info.remote_service_capabilities
                if remote_caps:
                    print(f"hazard_capable: {remote_caps.hazard_capable}")
                    print(f"vehicle_finder_capable: {remote_caps.vehicle_finder_capable}")
                    print(f"estart_enabled: {remote_caps.estart_enabled}")
                else:
                    print("remote_service_capabilities is None")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_vehicle())