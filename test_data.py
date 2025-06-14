#!/usr/bin/env python3
"""
Тестовые данные для демонстрации Toyota Dashboard
"""

import asyncio
import json
from datetime import datetime, timedelta

# Тестовые данные автомобиля
VEHICLE_DATA = {
    "vin": "JTPABACA90R004975",
    "model": "Toyota C-HR - NG '24",
    "date_of_first_use": "2024-05-23",
    "image": "https://dj3z27z47basa.cloudfront.net/3fd45119-ae71-4298-abd2-281907b01f73",
    "battery_level": 95,
    "fuel_level": 86,
    "range_electric": 74,
    "range_fuel": 459,
    "charging_status": "none",
    "remaining_charge_time": None,
    "location": {
        "latitude": 45.542026,
        "longitude": 13.713837,
        "address": "Копер, Словения",
        "country": "Slovenia"
    },
    "locked": True,
    "fuel_price": "1.43 €/л"
}

# Тестовые уведомления
NOTIFICATIONS = [
    {
        "category": "VehicleStatusAlert",
        "message": "JTPABACA90R004975 has multiple vehicle alerts, please check app for more details.",
        "date": "2025-06-14T07:12:22.398000Z",
        "type": "alert",
        "read": False
    },
    {
        "category": "ChargingAlert", 
        "message": "Toyota C-HR: Your car is fully charged to your set maximum percentage.",
        "date": "2025-06-14T02:20:03.438000Z",
        "type": "alert",
        "read": False
    },
    {
        "category": "ChargingAlert",
        "message": "Toyota C-HR: Your car is now charging.",
        "date": "2025-06-13T22:05:49.519000Z", 
        "type": "alert",
        "read": True
    },
    {
        "category": "RemoteCommand",
        "message": "JTPABACA90R004975 : You can only start climate for a total of 20 minutes between 2 ignition starts.",
        "date": "2025-06-13T11:53:02.882000Z",
        "type": "alert", 
        "read": True
    },
    {
        "category": "RemoteCommand",
        "message": "JTPABACA90R004975 : The vehicle is now unlocked.",
        "date": "2025-06-13T11:01:26.693000Z",
        "type": "alert",
        "read": True
    }
]

# Тестовая статистика
STATS_DATA = {
    "today": {
        "distance": 5.5,
        "fuel_consumed": 0.0,
        "electricity_consumed": 1.2,
        "fuel_cost": 0.00,
        "trips": 1
    },
    "week": {
        "distance": 45.2,
        "fuel_consumed": 2.1,
        "electricity_consumed": 8.5,
        "fuel_cost": 3.00,
        "trips": 8
    },
    "month": {
        "distance": 180.5,
        "fuel_consumed": 8.2,
        "electricity_consumed": 32.1,
        "fuel_cost": 11.73,
        "trips": 25
    }
}

def save_test_data():
    """Сохранить тестовые данные в файлы."""
    with open('/workspace/toyota-dashboard/test_vehicle_data.json', 'w', encoding='utf-8') as f:
        json.dump(VEHICLE_DATA, f, indent=2, ensure_ascii=False)
    
    with open('/workspace/toyota-dashboard/test_notifications.json', 'w', encoding='utf-8') as f:
        json.dump(NOTIFICATIONS, f, indent=2, ensure_ascii=False)
    
    with open('/workspace/toyota-dashboard/test_stats.json', 'w', encoding='utf-8') as f:
        json.dump(STATS_DATA, f, indent=2, ensure_ascii=False)
    
    print("Тестовые данные сохранены")

if __name__ == "__main__":
    save_test_data()