#!/usr/bin/env python3
"""
Toyota C-HR PHEV Dashboard Server
Персональный сервер для мониторинга и управления Toyota C-HR PHEV
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from pytoyoda import MyT
from pytoyoda.models.endpoints.command import CommandType
from database import DatabaseManager
from models import VehicleStatus, TripData, StatsPeriod

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/toyota-dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
def load_config() -> Dict:
    """Загрузить конфигурацию из файла."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Файл config.yaml не найден!")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Ошибка в config.yaml: {e}")
        raise

# Глобальные переменные
config = load_config()
app = FastAPI(title="Toyota C-HR PHEV Dashboard", version="1.0.0")
db = DatabaseManager(config['database']['path'])
toyota_client: Optional[MyT] = None
vehicle_vin = config['toyota']['vin']

# Настройка CORS для доступа с iPhone
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Модели данных
class CommandRequest(BaseModel):
    """Запрос на выполнение команды."""
    command: str
    duration: Optional[int] = None
    temperature: Optional[float] = None
    beeps: Optional[int] = 0

class StatsRequest(BaseModel):
    """Запрос статистики."""
    period: str  # day, week, month, year, all
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# Инициализация Toyota клиента
async def init_toyota_client():
    """Инициализировать подключение к Toyota API."""
    global toyota_client
    try:
        toyota_client = MyT(
            username=config['toyota']['username'],
            password=config['toyota']['password'],
            locale=config['dashboard'].get('language', 'ru'),
            region=config['toyota'].get('region', 'europe')
        )
        logger.info("Toyota клиент успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации Toyota клиента: {e}")
        raise

# Фоновые задачи
async def collect_vehicle_data():
    """Фоновая задача для сбора данных автомобиля."""
    while True:
        try:
            if toyota_client:
                # Получить статус автомобиля
                status = await toyota_client.get_vehicle_status(vehicle_vin)
                location = await toyota_client.get_vehicle_location(vehicle_vin)
                electric_status = await toyota_client.get_electric_status(vehicle_vin)
                
                # Сохранить в базу данных
                vehicle_data = VehicleStatus(
                    timestamp=datetime.now(),
                    battery_level=electric_status.battery_level,
                    fuel_level=status.fuel_level,
                    range_electric=electric_status.range_electric,
                    range_fuel=status.range_fuel,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    locked=status.locked,
                    engine_running=status.engine_running,
                    climate_on=status.climate_on,
                    temperature_inside=status.temperature_inside,
                    temperature_outside=status.temperature_outside
                )
                
                await db.save_vehicle_status(vehicle_data)
                logger.info("Данные автомобиля обновлены")
                
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
        
        # Ждать до следующего сбора
        await asyncio.sleep(config['monitoring']['data_collection_interval'])

# API маршруты

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда."""
    with open('static/index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/api/vehicle/status")
async def get_vehicle_status():
    """Получить текущий статус автомобиля."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        # Получить данные из API
        status = await toyota_client.get_vehicle_status(vehicle_vin)
        location = await toyota_client.get_vehicle_location(vehicle_vin)
        electric_status = await toyota_client.get_electric_status(vehicle_vin)
        
        return {
            "battery_level": electric_status.battery_level,
            "fuel_level": status.fuel_level,
            "range_electric": electric_status.range_electric,
            "range_fuel": status.range_fuel,
            "total_range": electric_status.range_electric + status.range_fuel,
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            },
            "locked": status.locked,
            "engine_running": status.engine_running,
            "climate_on": status.climate_on,
            "temperature_inside": status.temperature_inside,
            "temperature_outside": status.temperature_outside,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/lock")
async def lock_vehicle():
    """Заблокировать автомобиль."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        result = await toyota_client.send_command(vehicle_vin, CommandType.DOOR_LOCK)
        logger.info("Команда блокировки отправлена")
        
        return {"status": "success", "message": "Автомобиль заблокирован"}
    except Exception as e:
        logger.error(f"Ошибка блокировки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/unlock")
async def unlock_vehicle():
    """Разблокировать автомобиль."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        result = await toyota_client.send_command(vehicle_vin, CommandType.DOOR_UNLOCK)
        logger.info("Команда разблокировки отправлена")
        
        return {"status": "success", "message": "Автомобиль разблокирован"}
    except Exception as e:
        logger.error(f"Ошибка разблокировки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/start")
async def start_engine(request: CommandRequest):
    """Запустить двигатель (прогрев)."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        result = await toyota_client.send_command(vehicle_vin, CommandType.ENGINE_START)
        logger.info(f"Команда запуска двигателя отправлена на {request.duration} минут")
        
        return {"status": "success", "message": f"Двигатель запущен на {request.duration} минут"}
    except Exception as e:
        logger.error(f"Ошибка запуска двигателя: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/stop")
async def stop_engine():
    """Остановить двигатель."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        result = await toyota_client.send_command(vehicle_vin, CommandType.ENGINE_STOP)
        logger.info("Команда остановки двигателя отправлена")
        
        return {"status": "success", "message": "Двигатель остановлен"}
    except Exception as e:
        logger.error(f"Ошибка остановки двигателя: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/find")
async def find_vehicle():
    """Найти автомобиль (звуковой сигнал + мигание фар)."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        # Отправить команду поиска
        result = await toyota_client.send_command(vehicle_vin, CommandType.FIND_VEHICLE, beeps=3)
        logger.info("Команда поиска автомобиля отправлена")
        
        return {"status": "success", "message": "Автомобиль подает сигналы"}
    except Exception as e:
        logger.error(f"Ошибка поиска автомобиля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/climate")
async def control_climate(request: CommandRequest):
    """Управление климат-контролем."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        # Включить климат-контроль
        result = await toyota_client.send_command(vehicle_vin, CommandType.AC_SETTINGS_ON)
        logger.info(f"Климат-контроль включен, температура: {request.temperature}°C")
        
        return {
            "status": "success", 
            "message": f"Климат-контроль включен на {request.temperature}°C"
        }
    except Exception as e:
        logger.error(f"Ошибка управления климатом: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/phev")
async def get_phev_stats(period: str = "week"):
    """Получить статистику PHEV за период."""
    try:
        stats = await db.get_phev_statistics(period)
        
        return {
            "period": period,
            "total_distance": stats.get("total_distance", 0),
            "electric_distance": stats.get("electric_distance", 0),
            "fuel_distance": stats.get("fuel_distance", 0),
            "electric_percentage": stats.get("electric_percentage", 0),
            "fuel_consumption": stats.get("fuel_consumption", 0),
            "electricity_consumption": stats.get("electricity_consumption", 0),
            "co2_saved": stats.get("co2_saved", 0),
            "cost_savings": stats.get("cost_savings", 0)
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики PHEV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trips")
async def get_trips(limit: int = 10):
    """Получить последние поездки."""
    try:
        trips = await db.get_recent_trips(limit)
        return {"trips": trips}
    except Exception as e:
        logger.error(f"Ошибка получения поездок: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Проверка состояния сервера."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "toyota_client": toyota_client is not None,
        "database": await db.check_connection()
    }

# События приложения
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске."""
    logger.info("Запуск Toyota Dashboard Server...")
    
    # Создать директории
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Инициализировать базу данных
    await db.init_database()
    
    # Инициализировать Toyota клиент
    await init_toyota_client()
    
    # Запустить фоновый сбор данных
    if config['monitoring']['auto_refresh']:
        asyncio.create_task(collect_vehicle_data())
    
    logger.info("Toyota Dashboard Server запущен успешно!")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке."""
    logger.info("Остановка Toyota Dashboard Server...")
    await db.close()

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "app:app",
        host=config['server']['host'],
        port=config['server']['port'],
        reload=config['server']['debug'],
        log_level="info"
    )