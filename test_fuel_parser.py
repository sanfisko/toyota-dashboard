#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсинга цен с autotraveler.ru
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fuel_prices import fuel_price_service

async def test_fuel_parser():
    """Тестировать парсинг цен с сайта"""
    
    print("🔍 Тестирование парсинга цен с autotraveler.ru...")
    print("=" * 60)
    
    try:
        # Тест парсинга
        prices = await fuel_price_service.fetch_prices_from_autotraveler()
        
        if prices:
            print(f"✅ Успешно загружено цен для {len(prices)} стран:")
            print("-" * 60)
            
            # Сортируем по цене
            sorted_prices = sorted(prices.items(), key=lambda x: x[1]['gasoline'], reverse=True)
            
            for country_code, price_data in sorted_prices[:10]:  # Топ-10 самых дорогих
                country_name = fuel_price_service.get_country_name(country_code)
                gasoline = price_data['gasoline']
                electricity = price_data['electricity']
                print(f"{country_name:<20} {gasoline:.2f}€/л  {electricity:.2f}€/кВт⋅ч")
            
            print("-" * 60)
            print(f"Самые дешевые:")
            for country_code, price_data in sorted_prices[-5:]:  # Топ-5 самых дешевых
                country_name = fuel_price_service.get_country_name(country_code)
                gasoline = price_data['gasoline']
                print(f"{country_name:<20} {gasoline:.2f}€/л")
            
            # Тест обновления кэша
            print("\n🔄 Тестирование обновления кэша...")
            success = await fuel_price_service.update_prices_cache()
            if success:
                print("✅ Кэш успешно обновлен")
                
                # Проверка загрузки из кэша
                cached_prices = await fuel_price_service.load_cached_prices()
                if cached_prices:
                    print(f"✅ Из кэша загружено {len(cached_prices)} стран")
                else:
                    print("❌ Ошибка загрузки из кэша")
            else:
                print("❌ Ошибка обновления кэша")
            
            # Тест определения страны по координатам
            print("\n🌍 Тестирование определения страны...")
            
            # Словения (Ljubljana)
            slovenia_coords = (46.0569, 14.5058)
            country = await fuel_price_service.get_country_by_coordinates(*slovenia_coords)
            print(f"Координаты Любляны ({slovenia_coords}): {country}")
            
            if country == "SI":
                slovenia_prices = await fuel_price_service.get_fuel_prices(country_code="SI")
                print(f"Цены в Словении: бензин {slovenia_prices['gasoline']:.2f}€/л, электричество {slovenia_prices['electricity']:.2f}€/кВт⋅ч")
            
            # Германия (Berlin)
            germany_coords = (52.5200, 13.4050)
            country = await fuel_price_service.get_country_by_coordinates(*germany_coords)
            print(f"Координаты Берлина ({germany_coords}): {country}")
            
        else:
            print("❌ Не удалось загрузить цены с сайта")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fuel_parser())