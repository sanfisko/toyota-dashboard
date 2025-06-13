"""
Модуль для работы с базой данных Toyota Dashboard
"""

import sqlite3
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

from models import VehicleStatus, TripData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных для Toyota Dashboard."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def init_database(self):
        """Инициализировать базу данных и создать таблицы."""
        try:
            # Убеждаемся, что директория для базы данных существует
            import os
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except (PermissionError, OSError) as dir_error:
                    # Если не можем создать директорию, используем временную директорию
                    logger.warning(f"Не удалось создать директорию {db_dir}: {dir_error}")
                    from paths import paths
                    fallback_db_path = paths.get_temp_file('toyota.db')
                    logger.info(f"Используется временный путь к базе данных: {fallback_db_path}")
                    self.db_path = fallback_db_path
            
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info(f"База данных инициализирована: {self.db_path}")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    async def _create_tables(self):
        """Создать необходимые таблицы."""
        
        # Таблица статуса автомобиля
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                battery_level INTEGER,
                fuel_level INTEGER,
                range_electric INTEGER,
                range_fuel INTEGER,
                latitude REAL,
                longitude REAL,
                locked BOOLEAN,
                engine_running BOOLEAN,
                climate_on BOOLEAN,
                temperature_inside REAL,
                temperature_outside REAL,
                raw_data TEXT
            )
        """)
        
        # Таблица поездок
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                start_latitude REAL,
                start_longitude REAL,
                end_latitude REAL,
                end_longitude REAL,
                distance_total REAL,
                distance_electric REAL,
                distance_fuel REAL,
                fuel_consumed REAL,
                electricity_consumed REAL,
                avg_speed REAL,
                max_speed REAL,
                efficiency_score INTEGER,
                route_data TEXT
            )
        """)
        
        # Таблица команд
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                command_type TEXT NOT NULL,
                status TEXT NOT NULL,
                response_data TEXT,
                error_message TEXT
            )
        """)
        
        # Таблица уведомлений
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT FALSE,
                data TEXT
            )
        """)
        
        # Индексы для оптимизации
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_vehicle_status_timestamp 
            ON vehicle_status(timestamp)
        """)
        
        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_trips_start_time 
            ON trips(start_time)
        """)
        
        await self.connection.commit()
    
    async def save_vehicle_status(self, status: VehicleStatus):
        """Сохранить статус автомобиля."""
        try:
            await self.connection.execute("""
                INSERT INTO vehicle_status (
                    timestamp, battery_level, fuel_level, range_electric, range_fuel,
                    latitude, longitude, locked, engine_running, climate_on,
                    temperature_inside, temperature_outside, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status.timestamp,
                status.battery_level,
                status.fuel_level,
                status.range_electric,
                status.range_fuel,
                status.latitude,
                status.longitude,
                status.locked,
                status.engine_running,
                status.climate_on,
                status.temperature_inside,
                status.temperature_outside,
                json.dumps(status.raw_data) if status.raw_data else None
            ))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения статуса автомобиля: {e}")
            raise
    
    async def get_latest_status(self) -> Optional[Dict]:
        """Получить последний статус автомобиля."""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM vehicle_status 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = await cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка получения последнего статуса: {e}")
            return None
    
    async def get_phev_statistics(self, period: str) -> Dict:
        """Получить статистику автомобиля за период."""
        try:
            # Попробовать получить данные из Toyota API
            from toyota_client import toyota_client
            
            try:
                if not toyota_client.client:
                    await toyota_client.init_client()
                
                if toyota_client.client:
                    return await toyota_client.get_statistics_by_period(period)
            except Exception as api_error:
                logger.warning(f"Ошибка получения данных из Toyota API: {api_error}")
            
            # Fallback: использовать локальные данные из базы
            # Определить временной диапазон
            now = datetime.now()
            if period == "day" or period == "today":
                start_time = now - timedelta(days=1)
            elif period == "yesterday":
                start_time = now - timedelta(days=2)
            elif period == "week":
                start_time = now - timedelta(weeks=1)
            elif period == "month":
                start_time = now - timedelta(days=30)
            elif period == "year":
                start_time = now - timedelta(days=365)
            else:  # all
                start_time = datetime(2020, 1, 1)
            
            # Получить данные поездок за период
            cursor = await self.connection.execute("""
                SELECT 
                    SUM(distance_total) as total_distance,
                    SUM(distance_electric) as electric_distance,
                    SUM(distance_fuel) as fuel_distance,
                    SUM(fuel_consumed) as fuel_consumed,
                    SUM(electricity_consumed) as electricity_consumed,
                    AVG(efficiency_score) as avg_efficiency
                FROM trips 
                WHERE start_time >= ?
            """, (start_time,))
            
            row = await cursor.fetchone()
            
            if row and row[0]:  # Если есть данные
                total_distance = row[0] or 0
                electric_distance = row[1] or 0
                fuel_distance = row[2] or 0
                fuel_consumed = row[3] or 0
                electricity_consumed = row[4] or 0
                avg_efficiency = row[5] or 0
                
                # Расчеты
                electric_percentage = (electric_distance / total_distance * 100) if total_distance > 0 else 0
                
                # Экономия CO2 (примерно 2.3 кг CO2 на литр бензина)
                co2_saved = fuel_consumed * 2.3
                
                # Получить актуальные цены на топливо
                from fuel_prices import fuel_price_service
                
                # Попробовать определить местоположение из последних данных
                location_cursor = await self.connection.execute("""
                    SELECT latitude, longitude FROM vehicle_status 
                    WHERE latitude != 0 AND longitude != 0 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                location_row = await location_cursor.fetchone()
                
                if location_row:
                    prices = await fuel_price_service.get_fuel_prices(
                        latitude=location_row[0], 
                        longitude=location_row[1]
                    )
                else:
                    # Использовать дефолтные цены для Германии
                    prices = await fuel_price_service.get_fuel_prices("DE")
                
                # Расчет экономии в евро
                # Предполагаем средний расход топлива 6 л/100км для гибрида в режиме только бензин
                average_fuel_consumption_per_100km = 6.0
                
                # Стоимость, если бы весь путь проехали только на бензине
                fuel_cost_if_only_gasoline = (total_distance / 100) * average_fuel_consumption_per_100km * prices["gasoline"]
                
                # Фактическая стоимость (топливо + электричество)
                actual_fuel_cost = fuel_consumed * prices["gasoline"]
                actual_electric_cost = electricity_consumed * prices["electricity"]
                actual_total_cost = actual_fuel_cost + actual_electric_cost
                
                # Экономия = что потратили бы только на бензине - что потратили фактически
                cost_savings = max(0, fuel_cost_if_only_gasoline - actual_total_cost)
                
                return {
                    "total_distance": round(total_distance, 1),
                    "electric_distance": round(electric_distance, 1),
                    "fuel_distance": round(fuel_distance, 1),
                    "electric_percentage": round(electric_percentage, 1),
                    "fuel_consumption": round(fuel_consumed, 2),
                    "electricity_consumption": round(electricity_consumed, 2),
                    "co2_saved": round(co2_saved, 1),
                    "cost_savings": round(cost_savings, 0),
                    "avg_efficiency": round(avg_efficiency, 0)
                }
            else:
                # Возвращаем нулевые значения, если нет данных
                return {
                    "total_distance": 0,
                    "electric_distance": 0,
                    "fuel_distance": 0,
                    "electric_percentage": 0,
                    "fuel_consumption": 0,
                    "electricity_consumption": 0,
                    "co2_saved": 0,
                    "cost_savings": 0,
                    "avg_efficiency": 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики автомобиля: {e}")
            raise
    
    async def get_phev_statistics_by_dates(self, date_from: str, date_to: str) -> Dict:
        """Получить статистику автомобиля за диапазон дат."""
        try:
            # Попробовать получить данные из Toyota API
            from toyota_client import toyota_client
            
            try:
                if not toyota_client.client:
                    await toyota_client.init_client()
                
                if toyota_client.client:
                    return await toyota_client.get_statistics_by_dates(date_from, date_to)
            except Exception as api_error:
                logger.warning(f"Ошибка получения данных из Toyota API: {api_error}")
            
            # Fallback: использовать локальные данные из базы
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)  # Включить конечную дату
            
            # Получить данные поездок за период
            cursor = await self.connection.execute("""
                SELECT 
                    SUM(distance_total) as total_distance,
                    SUM(distance_electric) as electric_distance,
                    SUM(distance_fuel) as fuel_distance,
                    SUM(fuel_consumed) as fuel_consumed,
                    SUM(electricity_consumed) as electricity_consumed,
                    AVG(efficiency_score) as avg_efficiency,
                    COUNT(*) as trip_count
                FROM trips 
                WHERE start_time >= ? AND start_time < ?
            """, (start_date, end_date))
            
            row = await cursor.fetchone()
            
            if row and row[0]:  # Если есть данные
                total_distance = row[0] or 0
                electric_distance = row[1] or 0
                fuel_distance = row[2] or 0
                fuel_consumed = row[3] or 0
                electricity_consumed = row[4] or 0
                avg_efficiency = row[5] or 0
                trip_count = row[6] or 0
                
                # Расчеты
                electric_percentage = (electric_distance / total_distance * 100) if total_distance > 0 else 0
                co2_saved = fuel_consumed * 2.3
                
                # Получить актуальные цены на топливо
                from fuel_prices import fuel_price_service
                prices = await fuel_price_service.get_fuel_prices("DE")  # Дефолт для диапазона дат
                
                # Расчет экономии в евро
                # Предполагаем средний расход топлива 6 л/100км для гибрида в режиме только бензин
                average_fuel_consumption_per_100km = 6.0
                
                # Стоимость, если бы весь путь проехали только на бензине
                fuel_cost_if_only_gasoline = (total_distance / 100) * average_fuel_consumption_per_100km * prices["gasoline"]
                
                # Фактическая стоимость (топливо + электричество)
                actual_fuel_cost = fuel_consumed * prices["gasoline"]
                actual_electric_cost = electricity_consumed * prices["electricity"]
                actual_total_cost = actual_fuel_cost + actual_electric_cost
                
                # Экономия = что потратили бы только на бензине - что потратили фактически
                cost_savings = max(0, fuel_cost_if_only_gasoline - actual_total_cost)
                
                return {
                    "period": f"с {date_from} по {date_to}",
                    "total_distance": total_distance,
                    "electric_distance": electric_distance,
                    "fuel_distance": fuel_distance,
                    "electric_percentage": electric_percentage,
                    "fuel_consumption": fuel_consumed,
                    "electricity_consumption": electricity_consumed,
                    "co2_saved": co2_saved,
                    "cost_savings": cost_savings,
                    "trip_count": trip_count
                }
            else:
                # Нет данных
                return {
                    "period": f"с {date_from} по {date_to}",
                    "total_distance": 0,
                    "electric_distance": 0,
                    "fuel_distance": 0,
                    "electric_percentage": 0,
                    "fuel_consumption": 0,
                    "electricity_consumption": 0,
                    "co2_saved": 0,
                    "cost_savings": 0,
                    "trip_count": 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики за период {date_from} - {date_to}: {e}")
            raise
    
    async def get_total_statistics(self) -> Dict:
        """Получить общую статистику за все время."""
        try:
            # Используем только локальные данные из базы для общей статистики
            # Toyota API не всегда возвращает корректные данные о расходе топлива
            cursor = await self.connection.execute("""
                SELECT 
                    SUM(distance_total) as total_distance,
                    SUM(distance_electric) as electric_distance,
                    SUM(fuel_consumed) as fuel_consumed,
                    SUM(electricity_consumed) as electricity_consumed,
                    COUNT(*) as trip_count
                FROM trips
            """)
            
            row = await cursor.fetchone()
            
            logger.info(f"Общая статистика из БД: {row}")
            
            if row and row[0]:
                total_distance = row[0] or 0
                electric_distance = row[1] or 0
                fuel_consumed = row[2] or 0
                electricity_consumed = row[3] or 0
                trip_count = row[4] or 0
                
                logger.info(f"Обработанные данные: distance={total_distance}, fuel={fuel_consumed}")
                
                electric_percentage = (electric_distance / total_distance * 100) if total_distance > 0 else 0
                co2_saved = fuel_consumed * 2.3
                
                # Получить актуальные цены на топливо
                from fuel_prices import fuel_price_service
                prices = await fuel_price_service.get_fuel_prices("DE")  # Дефолт для общей статистики
                
                # Расчет экономии в евро
                # Предполагаем средний расход топлива 6 л/100км для гибрида в режиме только бензин
                average_fuel_consumption_per_100km = 6.0
                
                # Стоимость, если бы весь путь проехали только на бензине
                fuel_cost_if_only_gasoline = (total_distance / 100) * average_fuel_consumption_per_100km * prices["gasoline"]
                
                # Фактическая стоимость (топливо + электричество)
                actual_fuel_cost = fuel_consumed * prices["gasoline"]
                actual_electric_cost = electricity_consumed * prices["electricity"]
                actual_total_cost = actual_fuel_cost + actual_electric_cost
                
                # Экономия = что потратили бы только на бензине - что потратили фактически
                cost_savings = max(0, fuel_cost_if_only_gasoline - actual_total_cost)
                
                result = {
                    "total_distance": total_distance,
                    "electric_percentage": electric_percentage,
                    "fuel_consumed": fuel_consumed,
                    "cost_savings": cost_savings
                }
                
                logger.info(f"Возвращаемая статистика: {result}")
                return result
            else:
                logger.warning("Нет данных в таблице trips для общей статистики")
                return {
                    "total_distance": 0,
                    "electric_percentage": 0,
                    "fuel_consumed": 0,
                    "cost_savings": 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения общей статистики: {e}")
            raise
    
    async def get_recent_trips(self, limit: int = 10) -> List[Dict]:
        """Получить последние поездки."""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM trips 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            trips = []
            for row in rows:
                trip = dict(zip(columns, row))
                # Преобразовать JSON данные
                if trip['route_data']:
                    trip['route_data'] = json.loads(trip['route_data'])
                trips.append(trip)
            
            return trips
        except Exception as e:
            logger.error(f"Ошибка получения поездок: {e}")
            return []
    
    async def get_trip_by_time(self, start_time: datetime) -> Dict:
        """Получить поездку по времени начала."""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM trips WHERE start_time = ?
            """, (start_time,))
            
            row = await cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'start_latitude': row[3],
                    'start_longitude': row[4],
                    'end_latitude': row[5],
                    'end_longitude': row[6],
                    'distance_total': row[7],
                    'distance_electric': row[8],
                    'distance_fuel': row[9],
                    'fuel_consumed': row[10],
                    'electricity_consumed': row[11],
                    'avg_speed': row[12],
                    'max_speed': row[13],
                    'efficiency_score': row[14],
                    'route_data': json.loads(row[15]) if row[15] else None
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения поездки: {e}")
            return None

    async def save_trip(self, trip_data: Dict):
        """Сохранить данные поездки."""
        try:
            await self.connection.execute("""
                INSERT INTO trips (
                    start_time, end_time, start_latitude, start_longitude,
                    end_latitude, end_longitude, distance_total, distance_electric,
                    distance_fuel, fuel_consumed, electricity_consumed,
                    avg_speed, max_speed, efficiency_score, route_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_data.get('start_time'),
                trip_data.get('end_time'),
                trip_data.get('start_latitude', 0.0),
                trip_data.get('start_longitude', 0.0),
                trip_data.get('end_latitude', 0.0),
                trip_data.get('end_longitude', 0.0),
                trip_data.get('distance_total', 0.0),
                trip_data.get('distance_electric', 0.0),
                trip_data.get('distance_total', 0.0) - trip_data.get('distance_electric', 0.0),  # distance_fuel
                trip_data.get('fuel_consumed', 0.0),
                trip_data.get('electricity_consumed', 0.0),
                trip_data.get('avg_speed', 0.0),
                trip_data.get('max_speed', 0.0),
                trip_data.get('efficiency_score', 0.0),
                json.dumps(trip_data.get('route_data')) if trip_data.get('route_data') else None
            ))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения поездки: {e}")
            raise
    
    async def save_command(self, command_type: str, status: str, response_data: Dict = None, error_message: str = None):
        """Сохранить выполненную команду."""
        try:
            await self.connection.execute("""
                INSERT INTO commands (timestamp, command_type, status, response_data, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                command_type,
                status,
                json.dumps(response_data) if response_data else None,
                error_message
            ))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения команды: {e}")
    
    async def add_notification(self, notification_type: str, title: str, message: str, data: Dict = None):
        """Добавить уведомление."""
        try:
            await self.connection.execute("""
                INSERT INTO notifications (timestamp, type, title, message, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                notification_type,
                title,
                message,
                json.dumps(data) if data else None
            ))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка добавления уведомления: {e}")
    
    async def get_unread_notifications(self) -> List[Dict]:
        """Получить непрочитанные уведомления."""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM notifications 
                WHERE read = FALSE 
                ORDER BY timestamp DESC
            """)
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            notifications = []
            for row in rows:
                notification = dict(zip(columns, row))
                if notification['data']:
                    notification['data'] = json.loads(notification['data'])
                notifications.append(notification)
            
            return notifications
        except Exception as e:
            logger.error(f"Ошибка получения уведомлений: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: int):
        """Отметить уведомление как прочитанное."""
        try:
            await self.connection.execute("""
                UPDATE notifications SET read = TRUE WHERE id = ?
            """, (notification_id,))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка отметки уведомления: {e}")
    
    async def get_daily_summary(self, date: datetime) -> Dict:
        """Получить сводку за день."""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            cursor = await self.connection.execute("""
                SELECT 
                    COUNT(*) as trip_count,
                    SUM(distance_total) as total_distance,
                    SUM(distance_electric) as electric_distance,
                    SUM(fuel_consumed) as fuel_consumed,
                    SUM(electricity_consumed) as electricity_consumed
                FROM trips 
                WHERE start_time >= ? AND start_time < ?
            """, (start_of_day, end_of_day))
            
            row = await cursor.fetchone()
            
            if row:
                return {
                    "date": date.strftime("%Y-%m-%d"),
                    "trip_count": row[0] or 0,
                    "total_distance": round(row[1] or 0, 1),
                    "electric_distance": round(row[2] or 0, 1),
                    "fuel_consumed": round(row[3] or 0, 2),
                    "electricity_consumed": round(row[4] or 0, 2)
                }
            else:
                return {
                    "date": date.strftime("%Y-%m-%d"),
                    "trip_count": 0,
                    "total_distance": 0,
                    "electric_distance": 0,
                    "fuel_consumed": 0,
                    "electricity_consumed": 0
                }
        except Exception as e:
            logger.error(f"Ошибка получения сводки за день: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 365):
        """Очистить старые данные."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Удалить старые статусы (оставить только последний за каждый день)
            await self.connection.execute("""
                DELETE FROM vehicle_status 
                WHERE timestamp < ? 
                AND id NOT IN (
                    SELECT MAX(id) 
                    FROM vehicle_status 
                    WHERE timestamp < ?
                    GROUP BY DATE(timestamp)
                )
            """, (cutoff_date, cutoff_date))
            
            # Удалить старые команды
            await self.connection.execute("""
                DELETE FROM commands WHERE timestamp < ?
            """, (cutoff_date,))
            
            # Удалить прочитанные уведомления старше 30 дней
            notification_cutoff = datetime.now() - timedelta(days=30)
            await self.connection.execute("""
                DELETE FROM notifications 
                WHERE timestamp < ? AND read = TRUE
            """, (notification_cutoff,))
            
            await self.connection.commit()
            logger.info(f"Очистка старых данных завершена (старше {days_to_keep} дней)")
            
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
    
    async def check_connection(self) -> bool:
        """Проверить соединение с базой данных."""
        try:
            await self.connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def close(self):
        """Закрыть соединение с базой данных."""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с базой данных закрыто")