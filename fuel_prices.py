"""
Модуль для получения актуальных цен на топливо по странам.

Автоматически обновляет цены с сайта autotraveler.ru раз в день.
Определяет местоположение автомобиля и использует цены соответствующей страны.
"""

import httpx
import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
import os

class FuelPriceService:
    """Сервис для получения актуальных цен на топливо"""
    
    def __init__(self):
        self.cache_file = "fuel_prices_cache.json"
        self.cache_duration = timedelta(days=1)  # Кэш на 1 день
        self.autotraveler_url = "https://autotraveler.ru/spravka/benzine-in-europe.html"
        # Актуальные цены на май 2025 (источник: autotraveler.ru)
        self.default_prices = {
            "DE": {"gasoline": 1.75, "electricity": 0.30},  # Германия
            "FR": {"gasoline": 1.64, "electricity": 0.25},  # Франция
            "IT": {"gasoline": 1.70, "electricity": 0.28},  # Италия
            "ES": {"gasoline": 1.45, "electricity": 0.26},  # Испания
            "NL": {"gasoline": 2.10, "electricity": 0.32},  # Нидерланды
            "BE": {"gasoline": 1.63, "electricity": 0.29},  # Бельгия
            "AT": {"gasoline": 1.58, "electricity": 0.27},  # Австрия
            "CH": {"gasoline": 1.79, "electricity": 0.35},  # Швейцария
            "PL": {"gasoline": 1.34, "electricity": 0.22},  # Польша
            "CZ": {"gasoline": 1.34, "electricity": 0.24},  # Чехия
            "HU": {"gasoline": 1.45, "electricity": 0.20},  # Венгрия
            "SK": {"gasoline": 1.47, "electricity": 0.23},  # Словакия
            "SI": {"gasoline": 1.41, "electricity": 0.25},  # Словения
            "HR": {"gasoline": 1.42, "electricity": 0.22},  # Хорватия
            "RO": {"gasoline": 1.36, "electricity": 0.18},  # Румыния
            "BG": {"gasoline": 1.21, "electricity": 0.16},  # Болгария
            "GR": {"gasoline": 1.73, "electricity": 0.24},  # Греция
            "PT": {"gasoline": 1.73, "electricity": 0.27},  # Португалия
            "FI": {"gasoline": 1.67, "electricity": 0.20},  # Финляндия
            "SE": {"gasoline": 1.42, "electricity": 0.35},  # Швеция
            "NO": {"gasoline": 1.76, "electricity": 0.15},  # Норвегия
            "DK": {"gasoline": 1.82, "electricity": 0.40},  # Дания
            "LU": {"gasoline": 1.46, "electricity": 0.28},  # Люксембург
            "IE": {"gasoline": 1.71, "electricity": 0.30},  # Ирландия
            "GB": {"gasoline": 1.92, "electricity": 0.35},  # Великобритания
            "RU": {"gasoline": 0.66, "electricity": 0.05},  # Россия
            # Дополнительные страны из таблицы
            "LV": {"gasoline": 1.51, "electricity": 0.22},  # Латвия
            "LT": {"gasoline": 1.38, "electricity": 0.21},  # Литва
            "EE": {"gasoline": 1.53, "electricity": 0.20},  # Эстония
            "IS": {"gasoline": 1.99, "electricity": 0.18},  # Исландия
            "MT": {"gasoline": 1.34, "electricity": 0.26},  # Мальта
            "CY": {"gasoline": 1.33, "electricity": 0.24},  # Кипр
            "MK": {"gasoline": 1.22, "electricity": 0.15},  # Северная Македония
            "RS": {"gasoline": 1.49, "electricity": 0.16},  # Сербия
            "ME": {"gasoline": 1.39, "electricity": 0.17},  # Черногория
            "BA": {"gasoline": 1.19, "electricity": 0.14},  # Босния и Герцеговина
            "AL": {"gasoline": 1.76, "electricity": 0.13},  # Албания
            "MD": {"gasoline": 1.17, "electricity": 0.12},  # Молдавия
        }
        
        # Маппинг названий стран с сайта на коды ISO
        self.country_mapping = {
            "Германия": "DE", "Франция": "FR", "Италия": "IT", "Испания": "ES",
            "Нидерланды": "NL", "Бельгия": "BE", "Австрия": "AT", "Швейцария": "CH",
            "Польша": "PL", "Чехия": "CZ", "Венгрия": "HU", "Словакия": "SK",
            "Словения": "SI", "Хорватия": "HR", "Румыния": "RO", "Болгария": "BG",
            "Греция": "GR", "Португалия": "PT", "Финляндия": "FI", "Швеция": "SE",
            "Норвегия": "NO", "Дания": "DK", "Люксембург": "LU", "Ирландия": "IE",
            "Великобритания": "GB", "Россия": "RU", "Латвия": "LV", "Литва": "LT",
            "Эстония": "EE", "Исландия": "IS", "Мальта": "MT", "Кипр": "CY",
            "Северная Македония": "MK", "Сербия": "RS", "Черногория": "ME",
            "Босния и Герцеговина": "BA", "Албания": "AL", "Молдавия": "MD"
        }
    
    async def fetch_prices_from_autotraveler(self) -> Dict[str, Dict[str, float]]:
        """Получить актуальные цены с сайта autotraveler.ru"""
        try:
            logger.info("Загружаем актуальные цены с autotraveler.ru...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.autotraveler_url)
                
                if response.status_code != 200:
                    logger.error(f"Ошибка загрузки сайта: {response.status_code}")
                    return {}
                
                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем таблицу с ценами
                table = soup.find('table')
                if not table:
                    logger.error("Таблица с ценами не найдена")
                    return {}
                
                prices = {}
                
                # Парсим строки таблицы
                rows = table.find_all('tr')[1:]  # Пропускаем заголовок
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Извлекаем название страны
                        country_cell = cells[1]
                        country_link = country_cell.find('a')
                        if country_link:
                            country_name = country_link.text.strip()
                        else:
                            country_name = country_cell.text.strip()
                        
                        # Извлекаем цену на бензин 95
                        gasoline_cell = cells[2]
                        gasoline_text = gasoline_cell.text.strip()
                        
                        # Парсим цену (формат: "€ 1.75" или "€ 1.75 (+ 0.01)")
                        gasoline_match = re.search(r'€\s*([\d,\.]+)', gasoline_text)
                        if gasoline_match:
                            gasoline_price = float(gasoline_match.group(1).replace(',', '.'))
                            
                            # Получаем код страны
                            country_code = self.country_mapping.get(country_name)
                            if country_code:
                                # Используем цену на электричество из дефолтных значений
                                electricity_price = self.default_prices.get(country_code, {}).get("electricity", 0.25)
                                
                                prices[country_code] = {
                                    "gasoline": gasoline_price,
                                    "electricity": electricity_price
                                }
                                
                                logger.debug(f"Загружена цена для {country_name} ({country_code}): {gasoline_price}€/л")
                
                logger.info(f"Загружено цен для {len(prices)} стран")
                return prices
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке цен с autotraveler.ru: {e}")
            return {}
    
    async def update_prices_cache(self) -> bool:
        """Обновить кэш цен с сайта"""
        try:
            # Загружаем новые цены
            new_prices = await self.fetch_prices_from_autotraveler()
            
            if not new_prices:
                logger.warning("Не удалось загрузить новые цены, используем дефолтные")
                new_prices = self.default_prices
            
            # Сохраняем в кэш
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "prices": new_prices,
                "source": "autotraveler.ru" if new_prices != self.default_prices else "default"
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Кэш цен обновлен: {len(new_prices)} стран")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления кэша цен: {e}")
            return False
    
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
            # Определить страну
            if not country_code and latitude and longitude:
                country_code = await self.get_country_by_coordinates(latitude, longitude)
            elif not country_code:
                country_code = "SI"  # По умолчанию Словения
            
            # Убедиться, что кэш актуален
            await self.ensure_fresh_cache()
            
            # Загрузить цены из кэша
            cached_prices = await self.load_cached_prices()
            if cached_prices and country_code in cached_prices:
                prices = cached_prices[country_code]
                logger.info(f"Используем актуальные цены для {country_code}: бензин {prices['gasoline']}€/л, электричество {prices['electricity']}€/кВт⋅ч")
                return prices
            
            # Использовать дефолтные цены
            if country_code in self.default_prices:
                prices = self.default_prices[country_code]
                logger.warning(f"Используем дефолтные цены для {country_code}: бензин {prices['gasoline']}€/л")
                return prices
            else:
                # Если страна не найдена, использовать цены Словении
                prices = self.default_prices["SI"]
                logger.warning(f"Страна {country_code} не найдена, используем цены Словении: {prices}")
                return prices
                
        except Exception as e:
            logger.error(f"Ошибка получения цен на топливо: {e}")
            # Возвращаем дефолтные цены Словении
            return self.default_prices["SI"]
    
    async def ensure_fresh_cache(self):
        """Убедиться, что кэш актуален (обновить при необходимости)"""
        try:
            # Проверить существование файла кэша
            if not os.path.exists(self.cache_file):
                logger.info("Кэш не найден, создаем новый")
                await self.update_prices_cache()
                return
            
            # Проверить возраст кэша
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data.get("timestamp", "2000-01-01"))
                if datetime.now() - cache_time > self.cache_duration:
                    logger.info(f"Кэш устарел (возраст: {datetime.now() - cache_time}), обновляем")
                    await self.update_prices_cache()
                else:
                    logger.debug(f"Кэш актуален (возраст: {datetime.now() - cache_time})")
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Поврежденный кэш, пересоздаем: {e}")
                await self.update_prices_cache()
                
        except Exception as e:
            logger.error(f"Ошибка проверки кэша: {e}")
    
    async def load_cached_prices(self) -> Optional[Dict]:
        """Загрузить цены из кэша"""
        try:
            if not os.path.exists(self.cache_file):
                return None
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            return cache_data.get("prices", {})
            
        except Exception as e:
            logger.error(f"Ошибка загрузки кэша: {e}")
            return None
    
    def get_country_name(self, country_code: str) -> str:
        """Получить название страны по коду"""
        country_names = {
            "DE": "Германия", "FR": "Франция", "IT": "Италия", "ES": "Испания",
            "NL": "Нидерланды", "BE": "Бельгия", "AT": "Австрия", "CH": "Швейцария",
            "PL": "Польша", "CZ": "Чехия", "HU": "Венгрия", "SK": "Словакия",
            "SI": "Словения", "HR": "Хорватия", "RO": "Румыния", "BG": "Болгария",
            "GR": "Греция", "PT": "Португалия", "FI": "Финляндия", "SE": "Швеция",
            "NO": "Норвегия", "DK": "Дания", "LU": "Люксембург", "IE": "Ирландия",
            "GB": "Великобритания", "RU": "Россия", "LV": "Латвия", "LT": "Литва",
            "EE": "Эстония", "IS": "Исландия", "MT": "Мальта", "CY": "Кипр",
            "MK": "Северная Македония", "RS": "Сербия", "ME": "Черногория",
            "BA": "Босния и Герцеговина", "AL": "Албания", "MD": "Молдавия"
        }
        return country_names.get(country_code, country_code)

# Глобальный экземпляр сервиса
fuel_price_service = FuelPriceService()