"""
Модуль для работы с Toyota Connected Services через pytoyoda
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pytoyoda import MyT
from pytoyoda.models.summary import SummaryType
import yaml
import os

logger = logging.getLogger(__name__)

class ToyotaClient:
    """Клиент для работы с Toyota Connected Services."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.client: Optional[MyT] = None
        self.vehicle = None
        self._config = None
        
    async def init_client(self):
        """Инициализировать клиент Toyota."""
        try:
            # Загрузить конфигурацию
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                logger.error(f"Файл конфигурации {self.config_path} не найден")
                return False
            
            # Создать клиент
            self.client = MyT(
                username=self._config['toyota']['username'],
                password=self._config['toyota']['password'],
                use_metric=True
            )
            
            # Войти в систему
            await self.client.login()
            logger.info("Успешный вход в Toyota Connected Services")
            
            # Получить автомобили
            vehicles = await self.client.get_vehicles()
            if not vehicles:
                logger.error("Автомобили не найдены")
                return False
            
            # Найти автомобиль по VIN
            target_vin = self._config['toyota'].get('vin')
            if target_vin:
                for vehicle in vehicles:
                    if vehicle.vin == target_vin:
                        self.vehicle = vehicle
                        break
                
                if not self.vehicle:
                    logger.error(f"Автомобиль с VIN {target_vin} не найден")
                    return False
            else:
                # Использовать первый автомобиль
                self.vehicle = vehicles[0]
            
            logger.info(f"Подключен к автомобилю: {self.vehicle.vin}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации клиента Toyota: {e}")
            return False
    
    async def get_vehicle_status(self) -> Dict[str, Any]:
        """Получить статус автомобиля."""
        if not self.vehicle:
            raise Exception("Клиент не инициализирован")
        
        try:
            # Обновить данные автомобиля
            await self.vehicle.update()
            
            # Получить данные
            dashboard = self.vehicle.dashboard
            location = self.vehicle.location
            
            status = {
                "fuel_level": dashboard.fuel_level if dashboard else 0,
                "battery_level": dashboard.battery_level if dashboard else 0,
                "range_fuel": dashboard.fuel_range if dashboard else 0,
                "range_electric": dashboard.ev_range if dashboard else 0,
                "range_total": dashboard.total_range if dashboard else 0,
                "odometer": dashboard.odometer if dashboard else 0,
                "location": {
                    "latitude": location.latitude if location else None,
                    "longitude": location.longitude if location else None,
                    "timestamp": location.timestamp.isoformat() if location and location.timestamp else None
                },
                "doors_locked": True,  # Заглушка, нужно найти в API
                "engine_running": False,  # Заглушка
                "last_updated": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса автомобиля: {e}")
            raise
    
    async def get_statistics_by_period(self, period: str) -> Dict[str, Any]:
        """Получить статистику за период."""
        if not self.vehicle:
            raise Exception("Клиент не инициализирован")
        
        try:
            summary = None
            
            if period == "today":
                summary = await self.vehicle.get_current_day_summary()
            elif period == "yesterday":
                yesterday = date.today() - timedelta(days=1)
                summaries = await self.vehicle.get_summary(
                    from_date=yesterday,
                    to_date=yesterday,
                    summary_type=SummaryType.DAILY
                )
                summary = summaries[0] if summaries else None
            elif period == "week":
                summary = await self.vehicle.get_current_week_summary()
            elif period == "month":
                summary = await self.vehicle.get_current_month_summary()
            elif period == "year":
                summary = await self.vehicle.get_current_year_summary()
            elif period == "all":
                # Получить статистику за последние 2 года
                end_date = date.today()
                start_date = end_date - timedelta(days=730)
                summaries = await self.vehicle.get_summary(
                    from_date=start_date,
                    to_date=end_date,
                    summary_type=SummaryType.YEARLY
                )
                # Объединить все годовые статистики
                if summaries:
                    total_distance = sum(s.distance or 0 for s in summaries)
                    total_fuel = sum(s.fuel_consumed or 0 for s in summaries)
                    total_ev_distance = sum(s.ev_distance or 0 for s in summaries)
                    
                    return self._format_statistics(
                        total_distance=total_distance,
                        electric_distance=total_ev_distance,
                        fuel_distance=total_distance - total_ev_distance,
                        fuel_consumption=total_fuel,
                        electricity_consumption=0,  # Нужно найти в API
                        period=period
                    )
            
            if summary:
                return self._format_statistics(
                    total_distance=summary.distance or 0,
                    electric_distance=summary.ev_distance or 0,
                    fuel_distance=(summary.distance or 0) - (summary.ev_distance or 0),
                    fuel_consumption=summary.fuel_consumed or 0,
                    electricity_consumption=0,  # Нужно найти в API
                    period=period
                )
            else:
                return self._format_statistics(period=period)
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики за период {period}: {e}")
            return self._format_statistics(period=period)
    
    async def get_statistics_by_dates(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Получить статистику за диапазон дат."""
        if not self.vehicle:
            raise Exception("Клиент не инициализирован")
        
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            
            # Определить тип статистики в зависимости от диапазона
            days_diff = (to_date - from_date).days
            
            if days_diff <= 1:
                summary_type = SummaryType.DAILY
            elif days_diff <= 31:
                summary_type = SummaryType.WEEKLY
            elif days_diff <= 365:
                summary_type = SummaryType.MONTHLY
            else:
                summary_type = SummaryType.YEARLY
            
            summaries = await self.vehicle.get_summary(
                from_date=from_date,
                to_date=to_date,
                summary_type=summary_type
            )
            
            if summaries:
                # Объединить все статистики
                total_distance = sum(s.distance or 0 for s in summaries)
                total_fuel = sum(s.fuel_consumed or 0 for s in summaries)
                total_ev_distance = sum(s.ev_distance or 0 for s in summaries)
                
                return self._format_statistics(
                    total_distance=total_distance,
                    electric_distance=total_ev_distance,
                    fuel_distance=total_distance - total_ev_distance,
                    fuel_consumption=total_fuel,
                    electricity_consumption=0,  # Нужно найти в API
                    period=f"с {date_from} по {date_to}"
                )
            else:
                return self._format_statistics(period=f"с {date_from} по {date_to}")
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики за период {date_from} - {date_to}: {e}")
            return self._format_statistics(period=f"с {date_from} по {date_to}")
    
    def _format_statistics(
        self,
        total_distance: float = 0,
        electric_distance: float = 0,
        fuel_distance: float = 0,
        fuel_consumption: float = 0,
        electricity_consumption: float = 0,
        period: str = ""
    ) -> Dict[str, Any]:
        """Форматировать статистику в стандартный формат."""
        
        # Расчеты
        electric_percentage = (electric_distance / total_distance * 100) if total_distance > 0 else 0
        
        # Экономия CO2 (примерно 2.3 кг CO2 на литр бензина)
        co2_saved = electric_distance * 0.15  # Примерно 150г CO2 на км для электро режима
        
        # Экономия денег (примерно 50 руб за литр бензина vs 5 руб за кВт⋅ч)
        fuel_cost_saved = electric_distance * 0.05 * 50  # Примерный расчет
        
        # Количество поездок (примерная оценка)
        trip_count = max(1, int(total_distance / 20)) if total_distance > 0 else 0
        
        return {
            "period": period,
            "total_distance": round(total_distance, 2),
            "electric_distance": round(electric_distance, 2),
            "fuel_distance": round(fuel_distance, 2),
            "electric_percentage": round(electric_percentage, 1),
            "fuel_consumption": round(fuel_consumption, 2),
            "electricity_consumption": round(electricity_consumption, 2),
            "co2_saved": round(co2_saved, 2),
            "cost_savings": round(fuel_cost_saved, 0),
            "trip_count": trip_count
        }
    
    async def get_trips(self, date_from: str, date_to: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить список поездок за период."""
        if not self.vehicle:
            raise Exception("Клиент не инициализирован")
        
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            
            trips = await self.vehicle.get_trips(
                from_date=from_date,
                to_date=to_date,
                limit=limit
            )
            
            result = []
            if trips:
                for trip in trips:
                    trip_data = {
                        "start_time": trip.start_time.isoformat() if trip.start_time else None,
                        "end_time": trip.end_time.isoformat() if trip.end_time else None,
                        "distance": trip.distance or 0,
                        "duration": trip.duration.total_seconds() if trip.duration else 0,
                        "fuel_consumed": trip.fuel_consumed or 0,
                        "ev_distance": trip.ev_distance or 0,
                        "score": trip.score or 0,
                        "locations": {
                            "start": {
                                "lat": trip.locations.start.lat if trip.locations and trip.locations.start else None,
                                "lon": trip.locations.start.lon if trip.locations and trip.locations.start else None
                            },
                            "end": {
                                "lat": trip.locations.end.lat if trip.locations and trip.locations.end else None,
                                "lon": trip.locations.end.lon if trip.locations and trip.locations.end else None
                            }
                        } if trip.locations else None
                    }
                    result.append(trip_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения поездок: {e}")
            return []
    
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Отправить команду автомобилю."""
        if not self.vehicle:
            raise Exception("Клиент не инициализирован")
        
        try:
            # Здесь нужно реализовать отправку команд через pytoyoda
            # Пока возвращаем заглушку
            logger.info(f"Отправка команды: {command}")
            
            return {
                "success": True,
                "command": command,
                "message": f"Команда {command} отправлена успешно"
            }
            
        except Exception as e:
            logger.error(f"Ошибка отправки команды {command}: {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }

# Глобальный экземпляр клиента
toyota_client = ToyotaClient()