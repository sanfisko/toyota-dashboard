"""
Модуль для получения актуальных цен на топливо по странам
"""

import httpx
import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime, timedelta
import json
import os

class FuelPriceService:
    """Сервис для получения актуальных цен на топливо"""
    
    def __init__(self):
        self.cache_file = "fuel_prices_cache.json"
        self.cache_duration = timedelta(hours=6)  # Кэш на 6 часов
        self.default_prices = {
            "DE": {"gasoline": 1.65, "electricity": 0.30},  # Германия
            "FR": {"gasoline": 1.70, "electricity": 0.25},  # Франция
            "IT": {"gasoline": 1.75, "electricity": 0.28},  # Италия
            "ES": {"gasoline": 1.55, "electricity": 0.26},  # Испания
            "NL": {"gasoline": 1.80, "electricity": 0.32},  # Нидерланды
            "BE": {"gasoline": 1.68, "electricity": 0.29},  # Бельгия
            "AT": {"gasoline": 1.45, "electricity": 0.27},  # Австрия
            "CH": {"gasoline": 1.55, "electricity": 0.35},  # Швейцария
            "PL": {"gasoline": 1.35, "electricity": 0.22},  # Польша
            "CZ": {"gasoline": 1.40, "electricity": 0.24},  # Чехия
            "HU": {"gasoline": 1.38, "electricity": 0.20},  # Венгрия
            "SK": {"gasoline": 1.42, "electricity": 0.23},  # Словакия
            "SI": {"gasoline": 1.48, "electricity": 0.25},  # Словения
            "HR": {"gasoline": 1.45, "electricity": 0.22},  # Хорватия
            "RO": {"gasoline": 1.30, "electricity": 0.18},  # Румыния
            "BG": {"gasoline": 1.25, "electricity": 0.16},  # Болгария
            "GR": {"gasoline": 1.60, "electricity": 0.24},  # Греция
            "PT": {"gasoline": 1.65, "electricity": 0.27},  # Португалия
            "FI": {"gasoline": 1.70, "electricity": 0.20},  # Финляндия
            "SE": {"gasoline": 1.75, "electricity": 0.35},  # Швеция
            "NO": {"gasoline": 1.85, "electricity": 0.15},  # Норвегия
            "DK": {"gasoline": 1.80, "electricity": 0.40},  # Дания
            "LU": {"gasoline": 1.50, "electricity": 0.28},  # Люксембург
            "IE": {"gasoline": 1.55, "electricity": 0.30},  # Ирландия
            "GB": {"gasoline": 1.60, "electricity": 0.35},  # Великобритания
            "RU": {"gasoline": 0.65, "electricity": 0.05},  # Россия
        }
    
    async def get_country_by_coordinates(self, latitude: float, longitude: float) -> str:
        """Определить страну по координатам"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Используем бесплатный API для геокодирования
                response = await client.get(
                    f"https://api.bigdatacloud.net/data/reverse-geocode-client",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "localityLanguage": "en"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    country_code = data.get("countryCode", "DE")
                    logger.info(f"Определена страна: {country_code} для координат {latitude}, {longitude}")
                    return country_code
                else:
                    logger.warning(f"Ошибка геокодирования: {response.status_code}")
                    return "DE"  # По умолчанию Германия
                    
        except Exception as e:
            logger.error(f"Ошибка определения страны: {e}")
            return "DE"  # По умолчанию Германия
    
    def load_cache(self) -> Optional[Dict]:
        """Загрузить кэш цен"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    
                # Проверить актуальность кэша
                cache_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
                if datetime.now() - cache_time < self.cache_duration:
                    return cache.get("prices", {})
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки кэша: {e}")
        
        return None
    
    def save_cache(self, prices: Dict):
        """Сохранить кэш цен"""
        try:
            cache = {
                "timestamp": datetime.now().isoformat(),
                "prices": prices
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")
    
    async def get_fuel_prices_api(self, country_code: str) -> Optional[Dict]:
        """Получить цены на топливо через API (заглушка для будущего расширения)"""
        try:
            # В будущем здесь можно добавить реальные API для получения цен
            # Например: https://api.collectapi.com/gasPrice/europe
            # Пока используем статические данные
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цен через API: {e}")
            return None
    
    async def get_fuel_prices(self, country_code: str = None, latitude: float = None, longitude: float = None) -> Dict:
        """Получить актуальные цены на топливо"""
        try:
            # Сначала проверить кэш
            cached_prices = self.load_cache()
            if cached_prices:
                logger.info("Используются кэшированные цены на топливо")
                
            # Определить страну
            if not country_code and latitude and longitude:
                country_code = await self.get_country_by_coordinates(latitude, longitude)
            elif not country_code:
                country_code = "DE"  # По умолчанию Германия
            
            # Попробовать получить актуальные цены через API
            api_prices = await self.get_fuel_prices_api(country_code)
            if api_prices:
                self.save_cache({country_code: api_prices})
                return api_prices
            
            # Использовать кэшированные цены, если есть
            if cached_prices and country_code in cached_prices:
                return cached_prices[country_code]
            
            # Использовать дефолтные цены
            if country_code in self.default_prices:
                prices = self.default_prices[country_code]
                logger.info(f"Используются дефолтные цены для {country_code}: {prices}")
                return prices
            else:
                # Если страна не найдена, использовать средние европейские цены
                prices = self.default_prices["DE"]
                logger.info(f"Страна {country_code} не найдена, используются цены Германии: {prices}")
                return prices
                
        except Exception as e:
            logger.error(f"Ошибка получения цен на топливо: {e}")
            # Возвращаем дефолтные цены Германии
            return self.default_prices["DE"]
    
    def get_country_name(self, country_code: str) -> str:
        """Получить название страны по коду"""
        country_names = {
            "DE": "Германия", "FR": "Франция", "IT": "Италия", "ES": "Испания",
            "NL": "Нидерланды", "BE": "Бельгия", "AT": "Австрия", "CH": "Швейцария",
            "PL": "Польша", "CZ": "Чехия", "HU": "Венгрия", "SK": "Словакия",
            "SI": "Словения", "HR": "Хорватия", "RO": "Румыния", "BG": "Болгария",
            "GR": "Греция", "PT": "Португалия", "FI": "Финляндия", "SE": "Швеция",
            "NO": "Норвегия", "DK": "Дания", "LU": "Люксембург", "IE": "Ирландия",
            "GB": "Великобритания", "RU": "Россия"
        }
        return country_names.get(country_code, country_code)

# Глобальный экземпляр сервиса
fuel_price_service = FuelPriceService()