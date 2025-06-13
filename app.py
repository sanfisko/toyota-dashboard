#!/usr/bin/env python3
"""
Toyota Dashboard Server
Персональный сервер для мониторинга и управления Toyota автомобилями
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Дополнительная настройка для предотвращения создания кэша в текущей директории
import tempfile
import shutil

# Создаем временную рабочую директорию для pytoyoda если нужно
temp_work_dir = None
original_cwd = None

if not os.access('.', os.W_OK):
    # Если текущая директория read-only, создаем временную рабочую директорию
    temp_work_dir = tempfile.mkdtemp(prefix='toyota-dashboard-work-')
    original_cwd = os.getcwd()
    os.chdir(temp_work_dir)
    print(f"Переключились на временную рабочую директорию: {temp_work_dir}")
    
    # Регистрируем функцию очистки при завершении
    import atexit
    def cleanup_temp_dir():
        if temp_work_dir and os.path.exists(temp_work_dir):
            try:
                if original_cwd:
                    os.chdir(original_cwd)
                shutil.rmtree(temp_work_dir)
                print(f"Временная рабочая директория удалена: {temp_work_dir}")
            except Exception as e:
                print(f"Ошибка при удалении временной директории: {e}")
    
    atexit.register(cleanup_temp_dir)

from pytoyoda import MyT
from pytoyoda.models.endpoints.command import CommandType
from database import DatabaseManager
from models import VehicleStatus, TripData, StatsPeriod
from paths import paths

# Настройка кэш-директории для предотвращения ошибок read-only filesystem
try:
    # Устанавливаем переменные окружения для кэша ПЕРЕД импортом pytoyoda
    os.environ["XDG_CACHE_HOME"] = os.path.dirname(paths.cache_dir)
    os.environ["HTTPX_CACHE_DIR"] = paths.cache_dir
    
    # Дополнительные переменные для различных библиотек
    os.environ["REQUESTS_CA_BUNDLE"] = ""  # Отключаем кэш сертификатов requests
    os.environ["CURL_CA_BUNDLE"] = ""      # Отключаем кэш сертификатов curl
    os.environ["TMPDIR"] = paths.temp_dir  # Устанавливаем временную директорию
    
    # Создаем кэш-директорию если она не существует
    os.makedirs(paths.cache_dir, exist_ok=True)
    
    print(f"Кэш-директория настроена: {paths.cache_dir}")
except (OSError, PermissionError) as e:
    print(f"Предупреждение: Не удалось настроить кэш-директорию: {e}")
    # Fallback - используем временную директорию
    temp_cache = paths.get_temp_file('cache')
    os.makedirs(temp_cache, exist_ok=True)
    os.environ["XDG_CACHE_HOME"] = os.path.dirname(temp_cache)
    os.environ["HTTPX_CACHE_DIR"] = temp_cache
    os.environ["TMPDIR"] = paths.temp_dir
    print(f"Используется временная кэш-директория: {temp_cache}")

# Базовые директории
APP_DIR = paths.app_dir

# Используем менеджер путей для всех директорий
LOG_DIR = paths.log_dir
DATA_DIR = paths.data_dir

# Загрузка конфигурации
def load_config() -> Dict:
    """Загрузить конфигурацию из файла."""
    try:
        with open(paths.config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Файл конфигурации не найден: {paths.config_file}")
        raise
    except yaml.YAMLError as e:
        print(f"Ошибка в файле конфигурации: {e}")
        raise

# Глобальные переменные
config = load_config()

# Настройка логирования на основе конфигурации
log_level = getattr(logging, config.get('logging', {}).get('level', 'INFO').upper())
logging.basicConfig(
    level=log_level,
    format=config.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
    handlers=[
        logging.FileHandler(paths.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка уровня логирования для pytoyoda (убираем DEBUG сообщения)
logging.getLogger('pytoyoda').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('hishel').setLevel(logging.ERROR)
logging.getLogger('uvicorn').setLevel(logging.ERROR)
logging.getLogger('uvicorn.access').setLevel(logging.ERROR)
logging.getLogger('uvicorn.error').setLevel(logging.ERROR)

# Отключаем все логи кроме ошибок для всех библиотек
for logger_name in ['asyncio', 'aiohttp', 'urllib3', 'requests']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Настройка loguru для pytoyoda (отключаем DEBUG логи)
try:
    from loguru import logger as loguru_logger
    # Удаляем все существующие обработчики loguru
    loguru_logger.remove()
    # Добавляем только обработчик для ошибок
    if log_level <= logging.ERROR:
        loguru_logger.add(sys.stderr, level="ERROR", format="{time} | {level} | {name}:{function}:{line} - {message}")
except ImportError:
    pass
app = FastAPI(title="Toyota Dashboard", version="1.0.0")

# Используем путь к базе данных из менеджера путей
db_path = paths.database_path
db = DatabaseManager(db_path)
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
app.mount("/static", StaticFiles(directory=f"{APP_DIR}/static"), name="static")

# Модели данных
class CommandRequest(BaseModel):
    """Запрос на выполнение команды."""
    command: Optional[str] = None
    duration: Optional[int] = None
    temperature: Optional[float] = None
    beeps: Optional[int] = 0

class StatsRequest(BaseModel):
    """Запрос статистики."""
    period: str  # day, week, month, year, all
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ConfigRequest(BaseModel):
    """Запрос на сохранение конфигурации."""
    username: str
    password: str
    vin: str
    region: str = "europe"
    port: int = 2025

class TestConnectionRequest(BaseModel):
    """Запрос на тестирование подключения."""
    username: str
    password: str
    vin: str
    region: str = "europe"

# Инициализация Toyota клиента
async def init_toyota_client():
    """Инициализировать подключение к Toyota API."""
    global toyota_client
    try:
        toyota_client = MyT(
            username=config['toyota']['username'],
            password=config['toyota']['password'],
            use_metric=config['dashboard'].get('units', 'metric') == 'metric'
        )
        # Toyota клиент успешно инициализирован
    except Exception as e:
        logger.error(f"Ошибка инициализации Toyota клиента: {e}")
        raise

# Вспомогательная функция для получения автомобиля
async def get_vehicle():
    """Получить объект автомобиля по VIN."""
    if not toyota_client:
        raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
    
    # Получить автомобили
    await toyota_client.login()
    vehicles = await toyota_client.get_vehicles()
    
    # Найти нужный автомобиль по VIN
    for vehicle in vehicles:
        if vehicle.vin == vehicle_vin:
            return vehicle
    
    raise HTTPException(status_code=404, detail=f"Автомобиль с VIN {vehicle_vin} не найден")

# Фоновые задачи
async def collect_vehicle_data():
    """Фоновая задача для сбора данных автомобиля."""
    while True:
        try:
            if toyota_client:
                # Получить автомобили
                await toyota_client.login()
                vehicles = await toyota_client.get_vehicles()
                
                # Найти нужный автомобиль по VIN
                target_vehicle = None
                for vehicle in vehicles:
                    if vehicle.vin == vehicle_vin:
                        target_vehicle = vehicle
                        break
                
                if target_vehicle:
                    # Обновить данные автомобиля
                    await target_vehicle.update()
                    
                    # Сохранить в базу данных
                    vehicle_data = VehicleStatus(
                        timestamp=datetime.now(),
                        battery_level=target_vehicle.electric_status.battery_level if target_vehicle.electric_status else 0,
                        fuel_level=target_vehicle.dashboard.fuel_level if target_vehicle.dashboard else 0,
                        range_electric=target_vehicle.electric_status.ev_range if target_vehicle.electric_status else 0,
                        range_fuel=target_vehicle.dashboard.fuel_range if target_vehicle.dashboard else 0,
                        latitude=target_vehicle.location.latitude if target_vehicle.location else 0.0,
                        longitude=target_vehicle.location.longitude if target_vehicle.location else 0.0,
                        locked=target_vehicle.lock_status.doors.driver_seat.locked if target_vehicle.lock_status and target_vehicle.lock_status.doors and target_vehicle.lock_status.doors.driver_seat else False,
                        engine_running=False,  # Нужно найти правильное поле
                        climate_on=False,  # Нужно найти правильное поле
                        temperature_inside=0.0,  # Нужно найти правильное поле
                        temperature_outside=0.0  # Нужно найти правильное поле
                    )
                    
                    await db.save_vehicle_status(vehicle_data)
                    # Данные автомобиля обновлены
                else:
                    logger.warning(f"Автомобиль с VIN {vehicle_vin} не найден")
                
        except OSError as e:
            if e.errno == 30:  # Read-only file system
                logger.warning(f"Файловая система только для чтения, пропускаем сбор данных: {e}")
            else:
                logger.error(f"Ошибка файловой системы при сборе данных: {e}")
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
        
        # Ждать до следующего сбора
        await asyncio.sleep(config['monitoring']['data_collection_interval'])

# API маршруты

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда."""
    # Проверить, настроен ли Toyota клиент
    if not toyota_client or not config.get('toyota', {}).get('username'):
        # Перенаправить на страницу настройки
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="0; url=/setup">
            <title>Перенаправление...</title>
        </head>
        <body>
            <p>Перенаправление на страницу настройки...</p>
            <script>window.location.href = '/setup';</script>
        </body>
        </html>
        """)
    
    with open(paths.get_static_file('index.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/setup", response_class=HTMLResponse)
async def setup_page():
    """Страница настройки."""
    with open(paths.get_static_file('setup.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/api/system/paths")
async def get_system_paths():
    """Получить информацию о путях системы."""
    return paths.get_info()

@app.get("/api/vehicle/status")
async def get_vehicle_status():
    """Получить текущий статус автомобиля."""
    try:
        target_vehicle = await get_vehicle()
        
        # Обновить данные автомобиля
        await target_vehicle.update()
        
        return {
            "battery_level": target_vehicle.electric_status.battery_level if target_vehicle.electric_status else 0,
            "fuel_level": target_vehicle.dashboard.fuel_level if target_vehicle.dashboard else 0,
            "range_electric": target_vehicle.electric_status.ev_range if target_vehicle.electric_status else 0,
            "range_fuel": target_vehicle.dashboard.fuel_range if target_vehicle.dashboard else 0,
            "total_range": (target_vehicle.electric_status.ev_range if target_vehicle.electric_status else 0) + (target_vehicle.dashboard.fuel_range if target_vehicle.dashboard else 0),
            "location": {
                "latitude": target_vehicle.location.latitude if target_vehicle.location else 0.0,
                "longitude": target_vehicle.location.longitude if target_vehicle.location else 0.0,
                "address": getattr(target_vehicle.location, 'address', 'Неизвестно') if target_vehicle.location else 'Неизвестно'
            },
            "locked": target_vehicle.lock_status.doors.driver_seat.locked if target_vehicle.lock_status and target_vehicle.lock_status.doors and target_vehicle.lock_status.doors.driver_seat else False,
            "engine_running": False,  # Нужно найти правильное поле
            "climate_on": False,  # Нужно найти правильное поле
            "temperature_inside": 0.0,  # Нужно найти правильное поле
            "temperature_outside": 0.0,  # Нужно найти правильное поле
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/lock")
async def lock_vehicle():
    """Заблокировать автомобиль."""
    try:
        target_vehicle = await get_vehicle()
        result = await target_vehicle.post_command(CommandType.DOOR_LOCK)
        # Команда блокировки отправлена
        
        return {"status": "success", "message": "Автомобиль заблокирован"}
    except Exception as e:
        logger.error(f"Ошибка блокировки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/unlock")
async def unlock_vehicle():
    """Разблокировать автомобиль."""
    try:
        target_vehicle = await get_vehicle()
        result = await target_vehicle.post_command(CommandType.DOOR_UNLOCK)
        # Команда разблокировки отправлена
        
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
        
        target_vehicle = await get_vehicle()
        
        result = await target_vehicle.post_command(CommandType.ENGINE_START)
        duration = request.duration if request.duration else 10
        # Команда запуска двигателя отправлена
        
        return {"status": "success", "message": f"Двигатель запущен на {duration} минут"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка запуска двигателя: {e}")
        # Проверяем, если это ошибка API Toyota
        if "Remote command interrupted" in str(e) or "40009" in str(e):
            raise HTTPException(status_code=400, detail="Команда запуска недоступна. Возможно, автомобиль уже заведен или команда не поддерживается.")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.post("/api/vehicle/stop")
async def stop_engine():
    """Остановить двигатель."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        target_vehicle = await get_vehicle()
        result = await target_vehicle.post_command(CommandType.ENGINE_STOP)
        # Команда остановки двигателя отправлена
        
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
        
        # Получить автомобили
        vehicles = await toyota_client.get_vehicles()
        if not vehicles:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        
        # Взять первый автомобиль
        vehicle = vehicles[0]
        
        # Отправить команду поиска
        result = await vehicle.post_command(CommandType.FIND_VEHICLE, beeps=3)
        # Команда поиска автомобиля отправлена
        
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
        
        target_vehicle = await get_vehicle()
        
        # Пробуем разные команды климат-контроля
        try:
            # Сначала пробуем AC_SETTINGS_ON
            result = await target_vehicle.post_command(CommandType.AC_SETTINGS_ON)
            # Климат-контроль включен
            return {
                "status": "success", 
                "message": "Климат-контроль включен"
            }
        except Exception as ac_error:
            logger.warning(f"AC_SETTINGS_ON не сработал: {ac_error}")
            
            # Пробуем VENTILATION_ON
            try:
                result = await target_vehicle.post_command(CommandType.VENTILATION_ON)
                # Вентиляция включена
                return {
                    "status": "success", 
                    "message": "Вентиляция включена"
                }
            except Exception as vent_error:
                logger.warning(f"VENTILATION_ON не сработал: {vent_error}")
                
                # Если ничего не работает, возвращаем информативную ошибку
                raise HTTPException(
                    status_code=400, 
                    detail=f"Климат-контроль недоступен. Возможные причины: автомобиль заведен, команда не поддерживается или временная ошибка API. Попробуйте позже."
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка управления климатом: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.post("/api/vehicle/windows/open")
async def open_windows():
    """Открыть окна автомобиля."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        target_vehicle = await get_vehicle()
        
        # Проверить возможности автомобиля
        extended_caps = target_vehicle._vehicle_info.extended_capabilities
        if not extended_caps or not extended_caps.power_windows_capable:
            raise HTTPException(
                status_code=400, 
                detail="Данный автомобиль не поддерживает дистанционное управление окнами"
            )
        
        # Отправить команду открытия окон
        result = await target_vehicle.post_command(CommandType.WINDOW_ON)
        # Команда открытия окон отправлена
        
        return {"status": "success", "message": "Окна открываются"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка открытия окон: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/windows/close")
async def close_windows():
    """Закрыть окна автомобиля."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        target_vehicle = await get_vehicle()
        
        # Проверить возможности автомобиля
        extended_caps = target_vehicle._vehicle_info.extended_capabilities
        if not extended_caps or not extended_caps.power_windows_capable:
            raise HTTPException(
                status_code=400, 
                detail="Данный автомобиль не поддерживает дистанционное управление окнами"
            )
        
        # Отправить команду закрытия окон
        result = await target_vehicle.post_command(CommandType.WINDOW_OFF)
        # Команда закрытия окон отправлена
        
        return {"status": "success", "message": "Окна закрываются"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка закрытия окон: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vehicle/capabilities")
async def get_vehicle_capabilities():
    """Получить возможности автомобиля."""
    try:
        if not toyota_client:
            raise HTTPException(status_code=503, detail="Toyota клиент не инициализирован")
        
        target_vehicle = await get_vehicle()
        extended_caps = target_vehicle._vehicle_info.extended_capabilities
        remote_caps = target_vehicle._vehicle_info.remote_service_capabilities
        
        return {
            "power_windows": extended_caps.power_windows_capable if extended_caps else False,
            "door_lock_unlock": extended_caps.door_lock_unlock_capable if extended_caps else False,
            "climate_control": extended_caps.climate_capable if extended_caps else False,
            "engine_start_stop": remote_caps.estart_enabled if remote_caps else False,
            "hazard_lights": remote_caps.hazard_capable if remote_caps else False,
            "vehicle_finder": remote_caps.vehicle_finder_capable if remote_caps else False,
            "trunk_control": remote_caps.trunk_capable if remote_caps else False,
            "horn": False,  # Horn capability not found in current API
            "headlights": remote_caps.head_light_capable if remote_caps else False
        }
    except Exception as e:
        logger.error(f"Ошибка получения возможностей автомобиля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/phev")
async def get_phev_stats(
    period: str = None,
    date_from: str = None,
    date_to: str = None
):
    """Получить статистику автомобиля за период или диапазон дат."""
    try:
        # Если указаны конкретные даты, используем их
        if date_from and date_to:
            stats = await db.get_phev_statistics_by_dates(date_from, date_to)
            period_label = f"с {date_from} по {date_to}"
        else:
            # Иначе используем предустановленный период
            if not period:
                period = "today"
            stats = await db.get_phev_statistics(period)
            period_label = period
        
        # Рассчитать дополнительные метрики
        total_distance = stats.get("total_distance", 0)
        fuel_consumption = stats.get("fuel_consumption", 0)
        electricity_consumption = stats.get("electricity_consumption", 0)
        
        # Количество поездок (заглушка, нужно будет получать из реальных данных)
        trip_count = stats.get("trip_count", 0)
        if trip_count == 0 and total_distance > 0:
            # Примерная оценка: одна поездка на каждые 20 км
            trip_count = max(1, int(total_distance / 20))
        
        return {
            "period": period_label,
            "total_distance": total_distance,
            "electric_distance": stats.get("electric_distance", 0),
            "fuel_distance": stats.get("fuel_distance", 0),
            "electric_percentage": stats.get("electric_percentage", 0),
            "fuel_consumption": fuel_consumption,
            "electricity_consumption": electricity_consumption,
            "co2_saved": stats.get("co2_saved", 0),
            "cost_savings": stats.get("cost_savings", 0),
            "trip_count": trip_count
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики автомобиля: {e}")
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

@app.get("/api/config")
async def get_config():
    """Получить текущую конфигурацию (без паролей)."""
    safe_config = {
        "toyota": {
            "username": config.get('toyota', {}).get('username', ''),
            "vin": config.get('toyota', {}).get('vin', ''),
            "region": config.get('toyota', {}).get('region', 'europe'),
            "password": "***" if config.get('toyota', {}).get('password') else ""
        },
        "server": {
            "port": config.get('server', {}).get('port', 2025),
            "host": config.get('server', {}).get('host', '0.0.0.0')
        }
    }
    return safe_config

@app.post("/api/test-connection")
async def test_connection(request: TestConnectionRequest):
    """Тестировать подключение к Toyota API."""
    try:
        # Создать временный клиент для тестирования
        test_client = MyT(
            username=request.username,
            password=request.password,
            use_metric=True
        )
        
        # Попробовать получить информацию об автомобиле
        vehicles = await test_client.get_vehicles()
        
        # Найти автомобиль по VIN
        target_vehicle = None
        for vehicle in vehicles:
            if vehicle.vin == request.vin:
                target_vehicle = vehicle
                break
        
        if not target_vehicle:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Автомобиль с VIN {request.vin} не найден в вашем аккаунте"
                }
            )
        
        return {
            "success": True,
            "vehicle_info": f"{target_vehicle.model} ({target_vehicle.year})",
            "message": "Подключение успешно!"
        }
        
    except Exception as e:
        logger.error(f"Ошибка тестирования подключения: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/save-config")
async def save_config(request: ConfigRequest):
    """Сохранить конфигурацию."""
    global config, toyota_client, vehicle_vin
    
    try:
        # Обновить конфигурацию
        config['toyota']['username'] = request.username
        config['toyota']['password'] = request.password
        config['toyota']['vin'] = request.vin
        config['toyota']['region'] = request.region
        config['server']['port'] = request.port
        
        # Сохранить в файл
        with open(paths.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        # Обновить глобальные переменные
        vehicle_vin = request.vin
        
        # Переинициализировать Toyota клиент
        await init_toyota_client()
        
        # Конфигурация сохранена и клиент переинициализирован
        
        # Если порт изменился, нужно перезапустить сервер
        current_port = config.get('server', {}).get('port', 2025)
        if request.port != current_port:
            # Порт изменен
            # В продакшене здесь должен быть перезапуск через systemd
            pass
            
        return {
            "success": True,
            "message": "Конфигурация сохранена успешно!",
            "restart_required": request.port != current_port
        }
        
    except Exception as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# API для тестирования функций автомобиля
@app.post("/api/test/command")
async def test_command(request: dict):
    """Тестировать команду управления автомобилем."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        command = request.get('command')
        beeps = request.get('beeps', 0)
        
        if not command:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Команда не указана"
                }
            )
        
        # Отправить команду
        result = await toyota_client._api.send_command(
            vin=vehicle_vin,
            command=CommandType(command),
            beeps=beeps
        )
        
        logger.info(f"Команда {command} отправлена: {result}")
        
        return {
            "success": True,
            "command": command,
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка выполнения команды {request.get('command', 'unknown')}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/test/window")
async def test_window_command(request: dict):
    """Тестировать управление отдельными окнами."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        window = request.get('window')
        action = request.get('action')
        
        if not window or not action:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Окно или действие не указано"
                }
            )
        
        # Пока что используем общие команды окон, так как индивидуальное управление
        # может не поддерживаться API
        if action == 'open':
            command = CommandType.WINDOW_ON
        else:
            command = CommandType.WINDOW_OFF
        
        result = await toyota_client._api.send_command(
            vin=vehicle_vin,
            command=command,
            beeps=0
        )
        
        logger.info(f"Команда окна {window} - {action} отправлена: {result}")
        
        return {
            "success": True,
            "window": window,
            "action": action,
            "note": "Использована общая команда окон (индивидуальное управление может не поддерживаться)",
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка управления окном {request.get('window', 'unknown')}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/climate/status")
async def test_climate_status():
    """Получить статус климат-контроля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_climate_status(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса климата: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/climate/settings")
async def test_climate_settings():
    """Получить настройки климат-контроля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_climate_settings(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения настроек климата: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/test/climate/settings")
async def test_update_climate_settings(request: dict):
    """Обновить настройки климат-контроля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        from pytoyoda.models.endpoints.climate import ClimateSettingsModel
        
        # Создать модель настроек климата
        settings = ClimateSettingsModel(
            temperature=request.get('temperature', 22),
            settings_on=request.get('settings_on', True),
            temperature_unit=request.get('temperature_unit', 'C')
        )
        
        result = await toyota_client._api.update_climate_settings(
            vin=vehicle_vin,
            settings=settings
        )
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка обновления настроек климата: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/test/climate/refresh")
async def test_refresh_climate_status():
    """Запросить обновление статуса климата с автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.refresh_climate_status(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка запроса обновления статуса климата: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/status")
async def test_vehicle_status():
    """Получить общий статус автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_remote_status(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса автомобиля: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/location")
async def test_location():
    """Получить местоположение автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_location(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения местоположения: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/electric")
async def test_electric_status():
    """Получить электрический статус автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_vehicle_electric_status(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения электрического статуса: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/telemetry")
async def test_telemetry():
    """Получить телеметрию автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_telemetry(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения телеметрии: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/notifications")
async def test_notifications():
    """Получить уведомления автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_notifications(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения уведомлений: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/test/service-history")
async def test_service_history():
    """Получить историю обслуживания автомобиля."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        result = await toyota_client._api.get_service_history(vin=vehicle_vin)
        
        return {
            "success": True,
            "data": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения истории обслуживания: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/stats/total")
async def get_total_stats():
    """Получить общую статистику за все время."""
    try:
        # Получить общую статистику из базы данных
        total_stats = await db.get_total_statistics()
        
        return {
            "success": True,
            "total_distance": total_stats.get("total_distance", 0),
            "electric_percentage": total_stats.get("electric_percentage", 0),
            "fuel_consumed": total_stats.get("fuel_consumed", 0),
            "cost_savings": total_stats.get("cost_savings", 0)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения общей статистики: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/fuel-prices")
async def get_current_fuel_prices():
    """Получить актуальные цены на топливо для текущего местоположения."""
    try:
        from fuel_prices import fuel_price_service
        
        # Получить последнее местоположение из базы данных
        last_status = await db.get_last_vehicle_status()
        
        if last_status and last_status.latitude != 0 and last_status.longitude != 0:
            # Определить страну по координатам
            country_code = await fuel_price_service.get_country_by_coordinates(
                last_status.latitude, last_status.longitude
            )
            prices = await fuel_price_service.get_fuel_prices(
                latitude=last_status.latitude, 
                longitude=last_status.longitude
            )
        else:
            # Использовать дефолтные цены для Германии
            country_code = "DE"
            prices = await fuel_price_service.get_fuel_prices("DE")
        
        country_name = fuel_price_service.get_country_name(country_code)
        
        return {
            "success": True,
            "country_code": country_code,
            "country_name": country_name,
            "gasoline_price": prices["gasoline"],
            "electricity_price": prices["electricity"],
            "currency": "EUR"
        }

    except Exception as e:
        logger.error(f"Ошибка получения цен на топливо: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/update-fuel-prices")
async def force_update_fuel_prices():
    """Принудительно обновить цены на топливо с сайта autotraveler.ru"""
    try:
        from fuel_prices import fuel_price_service
        
        # Принудительно обновить кэш
        success = await fuel_price_service.update_prices_cache()
        
        if success:
            # Загрузить обновленные цены
            cached_prices = await fuel_price_service.load_cached_prices()
            count = len(cached_prices) if cached_prices else 0
            
            return {
                "success": True,
                "message": f"Цены обновлены для {count} стран",
                "source": "autotraveler.ru",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Не удалось обновить цены с сайта"
                }
            )
        
    except Exception as e:
        logger.error(f"Ошибка принудительного обновления цен: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/add-test-data")
async def add_test_data():
    """Добавить тестовые данные для проверки статистики."""
    try:
        # Добавить несколько тестовых поездок
        test_trips = [
            {
                "start_time": "2024-01-01 08:00:00",
                "end_time": "2024-01-01 08:30:00",
                "distance_total": 25.5,
                "distance_electric": 15.0,
                "distance_fuel": 10.5,
                "fuel_consumed": 1.2,
                "electricity_consumed": 3.5,
                "avg_efficiency": 85
            },
            {
                "start_time": "2024-01-01 18:00:00", 
                "end_time": "2024-01-01 18:45:00",
                "distance_total": 35.2,
                "distance_electric": 20.0,
                "distance_fuel": 15.2,
                "fuel_consumed": 1.8,
                "electricity_consumed": 4.2,
                "avg_efficiency": 78
            },
            {
                "start_time": "2024-01-02 09:15:00",
                "end_time": "2024-01-02 10:00:00", 
                "distance_total": 42.8,
                "distance_electric": 25.0,
                "distance_fuel": 17.8,
                "fuel_consumed": 2.1,
                "electricity_consumed": 5.1,
                "avg_efficiency": 82
            }
        ]
        
        for trip in test_trips:
            await db.connection.execute("""
                INSERT INTO trips (
                    start_time, end_time, distance_total, distance_electric, 
                    distance_fuel, fuel_consumed, electricity_consumed, avg_efficiency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip["start_time"], trip["end_time"], trip["distance_total"],
                trip["distance_electric"], trip["distance_fuel"], 
                trip["fuel_consumed"], trip["electricity_consumed"], trip["avg_efficiency"]
            ))
        
        await db.connection.commit()
        
        return {
            "success": True,
            "message": f"Добавлено {len(test_trips)} тестовых поездок"
        }
        
    except Exception as e:
        logger.error(f"Ошибка добавления тестовых данных: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# Маршрут для страницы тестирования
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Страница тестирования функций автомобиля."""
    try:
        with open(os.path.join(APP_DIR, 'static', 'test.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Страница тестирования не найдена</h1>",
            status_code=404
        )

# Маршрут для страницы статистики
@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    """Страница детальной статистики."""
    try:
        with open(os.path.join(APP_DIR, 'static', 'stats.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Страница статистики не найдена</h1>",
            status_code=404
        )

@app.post("/api/command")
async def execute_command(request: dict):
    """Универсальный endpoint для выполнения команд управления автомобилем."""
    try:
        command = request.get('command')
        
        if not command:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Команда не указана"
                }
            )
        
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        # Получить автомобиль
        vehicles = await toyota_client.get_vehicles()
        target_vehicle = None
        for vehicle in vehicles:
            if vehicle.vin == vehicle_vin:
                target_vehicle = vehicle
                break
        
        if not target_vehicle:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"Автомобиль с VIN {vehicle_vin} не найден"
                }
            )
        
        # Маппинг команд на CommandType
        command_mapping = {
            # Основные команды (скорее всего работают)
            'door-lock': CommandType.DOOR_LOCK,
            'door-unlock': CommandType.DOOR_UNLOCK,
            'hazard-on': CommandType.HAZARD_ON,
            'hazard-off': CommandType.HAZARD_OFF,
            'find-vehicle': CommandType.FIND_VEHICLE,
            'sound-horn': CommandType.SOUND_HORN,
            
            # Управление окнами
            'power-window-on': CommandType.WINDOW_ON,
            'power-window-off': CommandType.WINDOW_OFF,
            
            # Индивидуальное управление окнами (экспериментально)
            'power-window-front-left-up': CommandType.WINDOW_ON,
            'power-window-front-left-down': CommandType.WINDOW_OFF,
            'power-window-front-right-up': CommandType.WINDOW_ON,
            'power-window-front-right-down': CommandType.WINDOW_OFF,
            'power-window-rear-left-up': CommandType.WINDOW_ON,
            'power-window-rear-left-down': CommandType.WINDOW_OFF,
            'power-window-rear-right-up': CommandType.WINDOW_ON,
            'power-window-rear-right-down': CommandType.WINDOW_OFF,
            
            # Двигатель
            'engine-start': CommandType.ENGINE_START,
            'engine-stop': CommandType.ENGINE_STOP,
            
            # Климат-контроль
            'ac-on': CommandType.AC_SETTINGS_ON,
            'ac-off': CommandType.AC_SETTINGS_ON,  # Может потребоваться другая команда
            'ventilation-on': CommandType.VENTILATION_ON,
            
            # Освещение
            'lights-on': CommandType.HEADLIGHT_ON,
            'lights-off': CommandType.HEADLIGHT_OFF,
            
            # Багажник
            'trunk-open': CommandType.TRUNK_UNLOCK,
            'trunk-close': CommandType.TRUNK_LOCK,
        }
        
        # Проверить, поддерживается ли команда
        if command not in command_mapping:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"Команда '{command}' не поддерживается или не реализована",
                    "note": "Эта команда может не поддерживаться Toyota API или требует дополнительной реализации"
                }
            )
        
        command_type = command_mapping[command]
        
        # Определить количество сигналов для некоторых команд
        beeps = 0
        if command in ['find-vehicle']:
            beeps = 3
        elif command in ['sound-horn']:
            beeps = 1
        
        # Выполнить команду
        logger.info(f"Выполнение команды: {command} -> {command_type}")
        
        if beeps > 0:
            result = await target_vehicle.post_command(command_type, beeps=beeps)
        else:
            result = await target_vehicle.post_command(command_type)
        
        logger.info(f"Команда {command} выполнена: {result}")
        
        # Специальные сообщения для некоторых команд
        special_messages = {
            'power-window-front-left-up': 'Команда отправлена для переднего левого окна (может использоваться общая команда окон)',
            'power-window-front-left-down': 'Команда отправлена для переднего левого окна (может использоваться общая команда окон)',
            'power-window-front-right-up': 'Команда отправлена для переднего правого окна (может использоваться общая команда окон)',
            'power-window-front-right-down': 'Команда отправлена для переднего правого окна (может использоваться общая команда окон)',
            'power-window-rear-left-up': 'Команда отправлена для заднего левого окна (может использоваться общая команда окон)',
            'power-window-rear-left-down': 'Команда отправлена для заднего левого окна (может использоваться общая команда окон)',
            'power-window-rear-right-up': 'Команда отправлена для заднего правого окна (может использоваться общая команда окон)',
            'power-window-rear-right-down': 'Команда отправлена для заднего правого окна (может использоваться общая команда окон)',
            'ac-off': 'Команда кондиционера отправлена (выключение может требовать отдельной команды)',
        }
        
        message = special_messages.get(command, f"Команда {command} выполнена успешно")
        
        return {
            "success": True,
            "command": command,
            "message": message,
            "result": result.model_dump() if hasattr(result, 'model_dump') else str(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка выполнения команды {request.get('command', 'unknown')}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "command": request.get('command', 'unknown')
            }
        )

@app.get("/test-all")
async def test_all_page():
    """Страница тестирования всех функций."""
    try:
        with open(paths.get_static_file('test_all.html'), 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Страница тестирования не найдена</h1>",
            status_code=404
        )

# События приложения
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске."""
    try:
        # Создать директории
        os.makedirs(f'{DATA_DIR}/data', exist_ok=True)
        
        # Инициализировать базу данных
        await db.init_database()
        
        # Инициализировать Toyota клиент
        await init_toyota_client()
        
        # Запустить фоновый сбор данных
        if config['monitoring']['auto_refresh']:
            asyncio.create_task(collect_vehicle_data())
    except Exception as e:
        logger.error(f"Ошибка при запуске Toyota Dashboard Server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке."""
    try:
        await db.close()
    except Exception as e:
        logger.error(f"Ошибка при остановке Toyota Dashboard Server: {e}")

def daily_fuel_price_updater():
    """Фоновая задача для ежедневного обновления цен на топливо"""
    def update_prices():
        try:
            from fuel_prices import fuel_price_service
            
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Обновляем цены
            success = loop.run_until_complete(fuel_price_service.update_prices_cache())
            
            if success:
                logger.info("✅ Автоматическое обновление цен на топливо выполнено успешно")
            else:
                logger.warning("⚠️ Не удалось автоматически обновить цены на топливо")
                
            loop.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоматического обновления цен: {e}")
    
    def scheduler():
        """Планировщик для ежедневного обновления"""
        while True:
            try:
                # Получаем текущее время
                now = datetime.now()
                
                # Планируем обновление на 6:00 утра следующего дня
                next_update = now.replace(hour=6, minute=0, second=0, microsecond=0)
                if next_update <= now:
                    next_update += timedelta(days=1)
                
                # Вычисляем время до следующего обновления
                sleep_seconds = (next_update - now).total_seconds()
                
                logger.info(f"📅 Следующее обновление цен на топливо: {next_update.strftime('%Y-%m-%d %H:%M:%S')} (через {sleep_seconds/3600:.1f} часов)")
                
                # Ждем до времени обновления
                time.sleep(sleep_seconds)
                
                # Выполняем обновление
                update_prices()
                
            except Exception as e:
                logger.error(f"Ошибка планировщика обновления цен: {e}")
                # Ждем час перед повторной попыткой
                time.sleep(3600)
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=scheduler, daemon=True)
    scheduler_thread.start()
    
    # Выполняем первое обновление при запуске (если кэш пустой)
    try:
        from fuel_prices import fuel_price_service
        if not os.path.exists(fuel_price_service.cache_file):
            logger.info("🔄 Выполняем первоначальное обновление цен на топливо...")
            
            # Создаем event loop для первого обновления
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(fuel_price_service.update_prices_cache())
            
            if success:
                logger.info("✅ Первоначальное обновление цен выполнено")
            else:
                logger.warning("⚠️ Не удалось выполнить первоначальное обновление цен")
                
            loop.close()
            
    except Exception as e:
        logger.error(f"Ошибка первоначального обновления цен: {e}")

if __name__ == "__main__":
    # Запускаем планировщик обновления цен
    daily_fuel_price_updater()
    
    # Запуск сервера
    uvicorn_log_level = config.get('logging', {}).get('level', 'INFO').lower()
    uvicorn.run(
        "app:app",
        host=config['server']['host'],
        port=config['server']['port'],
        reload=config['server']['debug'],
        log_level=uvicorn_log_level
    )