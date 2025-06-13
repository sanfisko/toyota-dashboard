#!/usr/bin/env python3
"""
Утилита для сравнения цен на топливо с реальными данными
"""

from fuel_prices import fuel_price_service

def compare_prices():
    """Сравнить наши цены с реальными данными"""
    
    # Реальные цены из autotraveler.ru (май 2025)
    real_prices = {
        "DE": 1.75, "FR": 1.64, "IT": 1.70, "ES": 1.45, "NL": 2.10,
        "BE": 1.63, "AT": 1.58, "CH": 1.79, "PL": 1.34, "CZ": 1.34,
        "HU": 1.45, "SK": 1.47, "SI": 1.41, "HR": 1.42, "RO": 1.36,
        "BG": 1.21, "GR": 1.73, "PT": 1.73, "FI": 1.67, "SE": 1.42,
        "NO": 1.76, "DK": 1.82, "LU": 1.46, "IE": 1.71, "GB": 1.92,
        "RU": 0.66
    }
    
    print("🔍 Сравнение цен на бензин 95 (€/л):")
    print("=" * 60)
    print(f"{'Страна':<20} {'Наши цены':<12} {'Реальные':<12} {'Разница':<10}")
    print("-" * 60)
    
    total_diff = 0
    count = 0
    
    for country_code, real_price in real_prices.items():
        our_price = fuel_price_service.default_prices[country_code]["gasoline"]
        diff = our_price - real_price
        country_name = fuel_price_service.get_country_name(country_code)
        
        status = "✅" if abs(diff) <= 0.05 else "⚠️" if abs(diff) <= 0.15 else "❌"
        
        print(f"{country_name:<20} {our_price:<12.2f} {real_price:<12.2f} {diff:+.2f} {status}")
        
        total_diff += abs(diff)
        count += 1
    
    avg_diff = total_diff / count
    print("-" * 60)
    print(f"Средняя абсолютная разница: {avg_diff:.3f}€/л")
    
    # Статистика точности
    accurate = sum(1 for code, real in real_prices.items() 
                  if abs(fuel_price_service.default_prices[code]["gasoline"] - real) <= 0.05)
    good = sum(1 for code, real in real_prices.items() 
              if abs(fuel_price_service.default_prices[code]["gasoline"] - real) <= 0.15)
    
    print(f"Точность ±5 центов: {accurate}/{count} ({accurate/count*100:.1f}%)")
    print(f"Точность ±15 центов: {good}/{count} ({good/count*100:.1f}%)")
    
    print("\n📊 Топ-5 самых дорогих стран:")
    sorted_countries = sorted(real_prices.items(), key=lambda x: x[1], reverse=True)
    for i, (code, price) in enumerate(sorted_countries[:5], 1):
        country_name = fuel_price_service.get_country_name(code)
        print(f"{i}. {country_name}: {price:.2f}€/л")
    
    print("\n💰 Топ-5 самых дешевых стран:")
    for i, (code, price) in enumerate(sorted_countries[-5:], 1):
        country_name = fuel_price_service.get_country_name(code)
        print(f"{i}. {country_name}: {price:.2f}€/л")

if __name__ == "__main__":
    compare_prices()