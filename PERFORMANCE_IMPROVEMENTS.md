# ⚡ Улучшения производительности

## 1. Кэширование данных автомобиля

### Создать cache.py:
```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class VehicleDataCache:
    def __init__(self, default_ttl: int = 30):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry['expires']:
                return entry['data']
            else:
                # Удалить устаревшие данные
                del self._cache[key]
        return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Сохранить данные в кэш."""
        ttl = ttl or self.default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = {
            'data': data,
            'expires': expires
        }
    
    async def clear(self) -> None:
        """Очистить весь кэш."""
        self._cache.clear()
    
    async def cleanup_expired(self) -> None:
        """Удалить устаревшие записи."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now >= entry['expires']
        ]
        for key in expired_keys:
            del self._cache[key]

# Глобальный экземпляр кэша
vehicle_cache = VehicleDataCache()

# Background task для очистки кэша
async def cache_cleanup_task():
    while True:
        await vehicle_cache.cleanup_expired()
        await asyncio.sleep(60)  # Очистка каждую минуту
```

### Обновить app.py для использования кэша:
```python
from cache import vehicle_cache

@app.get("/api/vehicle/status")
async def get_vehicle_status():
    """Получить статус автомобиля с кэшированием."""
    cache_key = f"vehicle_status_{vehicle_vin}"
    
    # Попробовать получить из кэша
    cached_data = await vehicle_cache.get(cache_key)
    if cached_data:
        logger.info("Возвращаем данные из кэша")
        return cached_data
    
    try:
        # Получить свежие данные от Toyota API
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota client not initialized")
        
        vehicles = await toyota_client.get_vehicles()
        vehicle = next((v for v in vehicles if v.vin == vehicle_vin), None)
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Получить детальную информацию
        status_data = {
            "vin": vehicle.vin,
            "model": vehicle.model_name,
            "battery_level": getattr(vehicle, 'battery_level', None),
            "fuel_level": getattr(vehicle, 'fuel_level', None),
            "odometer": getattr(vehicle, 'odometer', None),
            "location": {
                "latitude": getattr(vehicle, 'latitude', None),
                "longitude": getattr(vehicle, 'longitude', None)
            },
            "doors_locked": getattr(vehicle, 'doors_locked', None),
            "engine_running": getattr(vehicle, 'engine_running', None),
            "last_updated": datetime.now().isoformat()
        }
        
        # Сохранить в кэш на 30 секунд
        await vehicle_cache.set(cache_key, status_data, ttl=30)
        
        # Сохранить в базу данных
        await db.save_vehicle_status(status_data)
        
        return status_data
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса автомобиля: {e}")
        
        # Попробовать вернуть последние данные из БД
        last_status = await db.get_last_vehicle_status(vehicle_vin)
        if last_status:
            logger.info("Возвращаем последние данные из БД")
            return last_status
            
        raise HTTPException(status_code=500, detail=str(e))
```

## 2. Асинхронный HTTP клиент

### Создать http_client.py:
```python
import httpx
import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AsyncHTTPClient:
    def __init__(self, timeout: float = 30.0, max_connections: int = 10):
        self.timeout = timeout
        self.max_connections = max_connections
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_connections=self.max_connections)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Client not initialized")
        return await self._client.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Client not initialized")
        return await self._client.post(url, **kwargs)

# Глобальный HTTP клиент
http_client = AsyncHTTPClient()
```

## 3. Оптимизация базы данных

### Обновить database.py:
```python
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class DatabaseManager:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
    
    async def initialize(self):
        """Инициализировать пул соединений."""
        if self._initialized:
            return
        
        # Создать пул соединений
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.db_path)
            # Оптимизация SQLite
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=10000")
            await conn.execute("PRAGMA temp_store=MEMORY")
            await self._connections.put(conn)
        
        # Создать таблицы
        async with self.get_connection() as conn:
            await self.create_tables(conn)
        
        self._initialized = True
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Получить соединение из пула."""
        if not self._initialized:
            await self.initialize()
        
        conn = await self._connections.get()
        try:
            yield conn
        finally:
            await self._connections.put(conn)
    
    async def save_vehicle_status_batch(self, statuses: List[Dict]) -> None:
        """Сохранить несколько статусов одним запросом."""
        async with self.get_connection() as conn:
            await conn.executemany("""
                INSERT OR REPLACE INTO vehicle_status 
                (vin, timestamp, battery_level, fuel_level, odometer, 
                 latitude, longitude, doors_locked, engine_running, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    status['vin'],
                    status['timestamp'],
                    status.get('battery_level'),
                    status.get('fuel_level'),
                    status.get('odometer'),
                    status.get('location', {}).get('latitude'),
                    status.get('location', {}).get('longitude'),
                    status.get('doors_locked'),
                    status.get('engine_running'),
                    json.dumps(status)
                )
                for status in statuses
            ])
            await conn.commit()
    
    async def get_vehicle_status_optimized(self, vin: str, limit: int = 100) -> List[Dict]:
        """Оптимизированный запрос статусов с индексами."""
        async with self.get_connection() as conn:
            # Использовать индекс по VIN и timestamp
            cursor = await conn.execute("""
                SELECT data_json 
                FROM vehicle_status 
                WHERE vin = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (vin, limit))
            
            rows = await cursor.fetchall()
            return [json.loads(row[0]) for row in rows]
    
    async def create_indexes(self, conn: aiosqlite.Connection):
        """Создать индексы для оптимизации запросов."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vehicle_status_vin ON vehicle_status(vin)",
            "CREATE INDEX IF NOT EXISTS idx_vehicle_status_timestamp ON vehicle_status(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_vehicle_status_vin_timestamp ON vehicle_status(vin, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trips_vin ON trips(vin)",
            "CREATE INDEX IF NOT EXISTS idx_trips_start_time ON trips(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_commands_timestamp ON commands(timestamp)",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        await conn.commit()
```

## 4. Background Tasks для тяжелых операций

### Создать tasks.py:
```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self.tasks: List[asyncio.Task] = []
        self.running = False
    
    async def start(self):
        """Запустить фоновые задачи."""
        if self.running:
            return
        
        self.running = True
        
        # Запустить задачи
        self.tasks = [
            asyncio.create_task(self.periodic_data_collection()),
            asyncio.create_task(self.cleanup_old_data()),
            asyncio.create_task(self.cache_cleanup()),
            asyncio.create_task(self.health_check()),
        ]
        
        logger.info("Background tasks started")
    
    async def stop(self):
        """Остановить фоновые задачи."""
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Background tasks stopped")
    
    async def periodic_data_collection(self):
        """Периодический сбор данных автомобиля."""
        while self.running:
            try:
                # Собрать данные каждые 5 минут
                await self.collect_vehicle_data()
                await asyncio.sleep(300)  # 5 минут
            except Exception as e:
                logger.error(f"Error in periodic data collection: {e}")
                await asyncio.sleep(60)  # Повторить через минуту при ошибке
    
    async def collect_vehicle_data(self):
        """Собрать данные автомобиля в фоне."""
        try:
            if toyota_client and vehicle_vin:
                vehicles = await toyota_client.get_vehicles()
                vehicle = next((v for v in vehicles if v.vin == vehicle_vin), None)
                
                if vehicle:
                    status_data = {
                        "vin": vehicle.vin,
                        "timestamp": datetime.now().isoformat(),
                        "battery_level": getattr(vehicle, 'battery_level', None),
                        "fuel_level": getattr(vehicle, 'fuel_level', None),
                        "odometer": getattr(vehicle, 'odometer', None),
                        "location": {
                            "latitude": getattr(vehicle, 'latitude', None),
                            "longitude": getattr(vehicle, 'longitude', None)
                        },
                        "doors_locked": getattr(vehicle, 'doors_locked', None),
                        "engine_running": getattr(vehicle, 'engine_running', None),
                    }
                    
                    # Сохранить в БД
                    await db.save_vehicle_status(status_data)
                    
                    # Обновить кэш
                    cache_key = f"vehicle_status_{vehicle_vin}"
                    await vehicle_cache.set(cache_key, status_data, ttl=300)
                    
                    logger.debug("Vehicle data collected successfully")
        
        except Exception as e:
            logger.error(f"Error collecting vehicle data: {e}")
    
    async def cleanup_old_data(self):
        """Очистка старых данных."""
        while self.running:
            try:
                # Очистка каждый день в 2:00
                now = datetime.now()
                if now.hour == 2 and now.minute == 0:
                    await self.cleanup_database()
                
                await asyncio.sleep(3600)  # Проверять каждый час
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    async def cleanup_database(self):
        """Очистить старые данные из БД."""
        try:
            # Удалить данные старше 90 дней
            cutoff_date = datetime.now() - timedelta(days=90)
            
            async with db.get_connection() as conn:
                # Удалить старые статусы
                await conn.execute("""
                    DELETE FROM vehicle_status 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                # Удалить старые команды
                await conn.execute("""
                    DELETE FROM commands 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                await conn.commit()
                
            logger.info("Old data cleaned up successfully")
        
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
    
    async def cache_cleanup(self):
        """Очистка кэша."""
        while self.running:
            try:
                await vehicle_cache.cleanup_expired()
                await asyncio.sleep(300)  # Каждые 5 минут
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(300)
    
    async def health_check(self):
        """Проверка здоровья системы."""
        while self.running:
            try:
                # Проверить соединение с Toyota API
                if toyota_client:
                    await toyota_client.get_vehicles()
                
                # Проверить базу данных
                await db.health_check()
                
                logger.debug("Health check passed")
                await asyncio.sleep(600)  # Каждые 10 минут
                
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                await asyncio.sleep(300)  # Повторить через 5 минут при ошибке

# Глобальный менеджер задач
task_manager = BackgroundTaskManager()
```

### Обновить app.py для использования background tasks:
```python
from tasks import task_manager

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске."""
    logger.info("Starting Toyota Dashboard Server...")
    
    # Инициализировать базу данных
    await db.initialize()
    
    # Инициализировать Toyota клиент
    await init_toyota_client()
    
    # Запустить фоновые задачи
    await task_manager.start()
    
    logger.info("Server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке."""
    logger.info("Shutting down Toyota Dashboard Server...")
    
    # Остановить фоновые задачи
    await task_manager.stop()
    
    # Закрыть соединения
    if toyota_client:
        await toyota_client.close()
    
    logger.info("Server stopped")
```

## 5. Оптимизация API эндпоинтов

### Добавить пагинацию и фильтрацию:
```python
from fastapi import Query
from typing import Optional

@app.get("/api/vehicle/history")
async def get_vehicle_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_type: Optional[str] = None
):
    """Получить историю с пагинацией и фильтрацией."""
    try:
        offset = (page - 1) * limit
        
        # Построить фильтры
        filters = {"vin": vehicle_vin}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if data_type:
            filters["data_type"] = data_type
        
        # Получить данные с пагинацией
        history = await db.get_vehicle_history_paginated(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Получить общее количество
        total = await db.count_vehicle_history(filters)
        
        return {
            "data": history,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting vehicle history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/summary")
async def get_stats_summary():
    """Получить сводную статистику (кэшированную)."""
    cache_key = "stats_summary"
    
    # Попробовать получить из кэша (кэш на 1 час)
    cached_stats = await vehicle_cache.get(cache_key)
    if cached_stats:
        return cached_stats
    
    try:
        # Вычислить статистику
        stats = await db.calculate_summary_stats(vehicle_vin)
        
        # Сохранить в кэш на 1 час
        await vehicle_cache.set(cache_key, stats, ttl=3600)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 6. Мониторинг производительности

### Создать metrics.py:
```python
import time
from functools import wraps
from typing import Dict, List
import asyncio
import psutil
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    def __init__(self):
        self.request_times: List[float] = []
        self.api_call_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
    
    def record_request_time(self, duration: float):
        """Записать время выполнения запроса."""
        self.request_times.append(duration)
        # Хранить только последние 1000 запросов
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
    
    def record_api_call_time(self, endpoint: str, duration: float):
        """Записать время вызова API."""
        if endpoint not in self.api_call_times:
            self.api_call_times[endpoint] = []
        
        self.api_call_times[endpoint].append(duration)
        # Хранить только последние 100 вызовов для каждого endpoint
        if len(self.api_call_times[endpoint]) > 100:
            self.api_call_times[endpoint] = self.api_call_times[endpoint][-100:]
    
    def record_error(self, error_type: str):
        """Записать ошибку."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_stats(self) -> Dict:
        """Получить статистику производительности."""
        stats = {
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "requests": {
                "total": len(self.request_times),
                "avg_time": sum(self.request_times) / len(self.request_times) if self.request_times else 0,
                "max_time": max(self.request_times) if self.request_times else 0,
                "min_time": min(self.request_times) if self.request_times else 0
            },
            "api_calls": {},
            "errors": self.error_counts
        }
        
        # Статистика по API вызовам
        for endpoint, times in self.api_call_times.items():
            if times:
                stats["api_calls"][endpoint] = {
                    "total": len(times),
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times)
                }
        
        return stats

# Глобальный экземпляр метрик
metrics = PerformanceMetrics()

def measure_time(func_name: str = None):
    """Декоратор для измерения времени выполнения."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                metrics.record_error(type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                name = func_name or func.__name__
                metrics.record_api_call_time(name, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                metrics.record_error(type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                name = func_name or func.__name__
                metrics.record_api_call_time(name, duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Middleware для измерения времени запросов
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    metrics.record_request_time(duration)
    response.headers["X-Process-Time"] = str(duration)
    
    return response

# Эндпоинт для получения метрик
@app.get("/api/metrics")
async def get_metrics():
    """Получить метрики производительности."""
    return metrics.get_stats()
```

Эти улучшения значительно повысят производительность и отзывчивость системы.