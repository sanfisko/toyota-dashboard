#!/usr/bin/env python3
"""
Сервис для определения местоположения и цен на топливо
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Актуальные цены на топливо 95 в Европе (€/л) - обновлено июнь 2024
FUEL_PRICES_EU = {
    "Slovenia": 1.43,
    "Italy": 1.65,
    "France": 1.58,
    "Spain": 1.42,
    "Germany": 1.71,
    "Austria": 1.48,
    "Croatia": 1.41,
    "Switzerland": 1.62,
    "Netherlands": 1.89,
    "Belgium": 1.67,
    "Portugal": 1.52,
    "Czech Republic": 1.35,
    "Hungary": 1.38,
    "Poland": 1.32,
    "Slovakia": 1.44,
    "Luxembourg": 1.45,
    "Denmark": 1.75,
    "Sweden": 1.68,
    "Norway": 1.85,
    "Finland": 1.72
}

# Известные города и их страны для быстрого поиска
KNOWN_CITIES = {
    "Koper": "Slovenia",
    "Копер": "Slovenia",
    "Trieste": "Italy",
    "Триест": "Italy",
    "Saint-Jean-de-Luz": "France",
    "Сен-Жан-де-Люз": "France",
    "Bilbao": "Spain",
    "Бильбао": "Spain",
    "Ljubljana": "Slovenia",
    "Venice": "Italy",
    "Венеция": "Italy",
    "Nice": "France",
    "Ницца": "France",
    "Barcelona": "Spain",
    "Барселона": "Spain",
    "Madrid": "Spain",
    "Мадрид": "Spain",
    "Paris": "France",
    "Париж": "France",
    "Rome": "Italy",
    "Рим": "Italy"
}

class LocationService:
    """Сервис для работы с местоположением и ценами на топливо."""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Получить HTTP сессию."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Закрыть HTTP сессию."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, str]:
        """
        Определить адрес по координатам.
        
        Args:
            latitude: Широта
            longitude: Долгота
            
        Returns:
            Словарь с информацией о местоположении
        """
        try:
            session = await self.get_session()
            
            # Используем OpenStreetMap Nominatim API
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "accept-language": "ru,en"
            }
            
            headers = {
                "User-Agent": "Toyota-Dashboard/1.0 (https://github.com/Harvardtabby2dv/toyota-dashboard)"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_nominatim_response(data)
                else:
                    logger.warning(f"Nominatim API error: {response.status}")
                    return self._get_fallback_location(latitude, longitude)
                    
        except Exception as e:
            logger.error(f"Ошибка геокодирования: {e}")
            return self._get_fallback_location(latitude, longitude)
    
    def _parse_nominatim_response(self, data: dict) -> Dict[str, str]:
        """Парсинг ответа от Nominatim API."""
        address = data.get("address", {})
        
        # Определяем город
        city = (address.get("city") or 
                address.get("town") or 
                address.get("village") or 
                address.get("municipality") or
                address.get("county") or
                "Неизвестный город")
        
        # Определяем страну
        country = address.get("country", "Неизвестная страна")
        country_code = address.get("country_code", "").upper()
        
        # Полный адрес
        display_name = data.get("display_name", f"{city}, {country}")
        
        return {
            "city": city,
            "country": country,
            "country_code": country_code,
            "address": display_name,
            "full_address": display_name
        }
    
    def _get_fallback_location(self, latitude: float, longitude: float) -> Dict[str, str]:
        """Резервное определение местоположения по координатам."""
        # Простое определение по известным координатам
        locations = [
            ((45.54, 13.71), "Копер, Словения", "Slovenia"),
            ((45.65, 13.77), "Триест, Италия", "Italy"),
            ((43.39, -1.50), "Сен-Жан-де-Люз, Франция", "France"),
            ((43.26, -2.93), "Бильбао, Испания", "Spain"),
        ]
        
        min_distance = float('inf')
        best_match = None
        
        for (lat, lon), address, country in locations:
            distance = ((latitude - lat) ** 2 + (longitude - lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                best_match = (address, country)
        
        if best_match and min_distance < 0.5:  # В пределах ~50км
            address, country = best_match
            city = address.split(",")[0]
            return {
                "city": city,
                "country": country,
                "country_code": "",
                "address": address,
                "full_address": address
            }
        
        return {
            "city": "Неизвестный город",
            "country": "Неизвестная страна", 
            "country_code": "",
            "address": f"Координаты: {latitude:.4f}, {longitude:.4f}",
            "full_address": f"Координаты: {latitude:.4f}, {longitude:.4f}"
        }
    
    def get_fuel_price(self, country: str) -> Tuple[float, str]:
        """
        Получить цену на топливо для страны.
        
        Args:
            country: Название страны
            
        Returns:
            Кортеж (цена, валюта)
        """
        # Нормализация названия страны
        country_normalized = country.strip()
        
        # Словарь для перевода названий стран
        country_mapping = {
            "Словения": "Slovenia",
            "Италия": "Italy", 
            "Франция": "France",
            "Испания": "Spain",
            "Германия": "Germany",
            "Австрия": "Austria",
            "Хорватия": "Croatia",
            "Швейцария": "Switzerland",
            "Нидерланды": "Netherlands",
            "Бельгия": "Belgium",
            "Португалия": "Portugal",
            "Чехия": "Czech Republic",
            "Венгрия": "Hungary",
            "Польша": "Poland",
            "Словакия": "Slovakia",
            "Люксембург": "Luxembourg",
            "Дания": "Denmark",
            "Швеция": "Sweden",
            "Норвегия": "Norway",
            "Финляндия": "Finland"
        }
        
        # Попробуем найти по русскому названию
        english_name = country_mapping.get(country_normalized)
        if english_name:
            country_normalized = english_name
        
        # Поиск в базе цен
        price = FUEL_PRICES_EU.get(country_normalized)
        
        if price is None:
            # Попробуем найти по частичному совпадению
            for country_key, country_price in FUEL_PRICES_EU.items():
                if (country_key.lower() in country_normalized.lower() or 
                    country_normalized.lower() in country_key.lower()):
                    price = country_price
                    break
        
        if price is None:
            # Средняя цена по Европе как fallback
            price = 1.55
            logger.warning(f"Цена топлива для {country} не найдена, используется средняя цена")
        
        return price, "€/л"
    
    async def get_location_info(self, latitude: float, longitude: float) -> Dict:
        """
        Получить полную информацию о местоположении включая цены на топливо.
        
        Args:
            latitude: Широта
            longitude: Долгота
            
        Returns:
            Словарь с информацией о местоположении и ценах
        """
        # Получаем информацию о местоположении
        location_info = await self.reverse_geocode(latitude, longitude)
        
        # Получаем цену на топливо
        fuel_price, currency = self.get_fuel_price(location_info["country"])
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "city": location_info["city"],
            "country": location_info["country"],
            "address": location_info["address"],
            "fuel_price": fuel_price,
            "fuel_currency": currency,
            "fuel_price_formatted": f"{fuel_price} {currency}"
        }

# Глобальный экземпляр сервиса
location_service = LocationService()

async def test_locations():
    """Тестирование различных местоположений."""
    test_coordinates = [
        (45.542026, 13.713837, "Копер, Словения"),
        (45.6495, 13.7768, "Триест, Италия"), 
        (43.3884, -1.5014, "Сен-Жан-де-Люз, Франция"),
        (43.2627, -2.9253, "Бильбао, Испания")
    ]
    
    print("🗺️  Тестирование определения местоположения и цен на топливо:\n")
    
    for lat, lon, expected in test_coordinates:
        print(f"📍 Координаты: {lat}, {lon}")
        print(f"   Ожидается: {expected}")
        
        location_info = await location_service.get_location_info(lat, lon)
        
        print(f"   Определено: {location_info['address']}")
        print(f"   Цена топлива: {location_info['fuel_price_formatted']}")
        print()
    
    await location_service.close()

if __name__ == "__main__":
    asyncio.run(test_locations())