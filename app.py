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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

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
from location_service import location_service

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
        # Выводим диагностическую информацию о путях
        print("=== Диагностика путей конфигурации ===")
        print(f"Информация о путях: {paths.get_info()}")
        
        config_path = paths.config_file
        print(f"Основной путь к конфигурации: {config_path}")
        
        # Проверяем доступность директории для записи
        config_dir = os.path.dirname(config_path)
        print(f"Директория конфигурации: {config_dir}")
        print(f"Директория существует: {os.path.exists(config_dir)}")
        if os.path.exists(config_dir):
            print(f"Права на запись в директорию: {os.access(config_dir, os.W_OK)}")
        
        if not os.path.exists(config_path):
            print(f"Файл конфигурации не найден: {config_path}")
            # Попробуем найти конфигурацию в других местах
            alternative_paths = [
                '/etc/toyota-dashboard/config.yaml',
                '/opt/toyota-dashboard/config.yaml',
                os.path.join(os.path.expanduser('~'), '.config', 'toyota-dashboard', 'config.yaml'),
                os.path.join(paths.app_dir, 'config.yaml')
            ]
            
            print("Поиск альтернативных путей:")
            for alt_path in alternative_paths:
                exists = os.path.exists(alt_path)
                print(f"  {alt_path}: {'найден' if exists else 'не найден'}")
                if exists:
                    try:
                        # Проверяем возможность чтения
                        with open(alt_path, 'r') as test_f:
                            test_f.read(1)
                        print(f"Используем альтернативный файл конфигурации: {alt_path}")
                        config_path = alt_path
                        break
                    except Exception as e:
                        print(f"  Ошибка чтения {alt_path}: {e}")
            else:
                print("Конфигурационный файл не найден ни в одном из ожидаемых мест")
                print("Создаем базовую конфигурацию...")
                return create_default_config()
        
        print(f"Попытка чтения конфигурации из: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            print(f"✅ Конфигурация успешно загружена из: {config_path}")
            return config_data
            
    except yaml.YAMLError as e:
        print(f"❌ Ошибка в файле конфигурации: {e}")
        raise
    except Exception as e:
        print(f"❌ Неожиданная ошибка при загрузке конфигурации: {e}")
        return create_default_config()

def create_default_config() -> Dict:
    """Создать базовую конфигурацию по умолчанию."""
    return {
        'toyota': {
            'username': '',
            'password': '',
            'vin': '',
            'region': 'europe'
        },
        'server': {
            'host': '0.0.0.0',
            'port': 2025,
            'secret_key': 'default-secret-key-change-me'
        },
        'database': {
            'path': paths.database_path
        },
        'logging': {
            'level': 'INFO',
            'file': paths.log_file
        }
    }

# Глобальные переменные
config = load_config()

# Настройка логирования на основе конфигурации
log_level = getattr(logging, config.get('logging', {}).get('level', 'INFO').upper())

# Настройка обработчиков логирования с проверкой доступности
handlers = [logging.StreamHandler()]  # Всегда добавляем консольный вывод

# Пытаемся добавить файловый обработчик
try:
    log_file_path = paths.log_file
    log_dir = os.path.dirname(log_file_path)
    
    # Создаем директорию логов если нужно
    os.makedirs(log_dir, exist_ok=True)
    
    # Проверяем возможность записи
    if os.access(log_dir, os.W_OK):
        handlers.append(logging.FileHandler(log_file_path))
        print(f"✅ Логирование в файл: {log_file_path}")
    else:
        print(f"⚠️ Нет прав на запись в директорию логов: {log_dir}")
        print("Логирование будет только в консоль")
        
except (OSError, PermissionError) as e:
    print(f"⚠️ Не удалось настроить файловое логирование: {e}")
    print("Логирование будет только в консоль")

logging.basicConfig(
    level=log_level,
    format=config.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
    handlers=handlers
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
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    try:
        # Убеждаемся, что все директории созданы
        paths.ensure_directories()
        
        # Инициализировать базу данных
        await db.init_database()
        
        # Инициализировать Toyota клиент
        await init_toyota_client()
        
        # Запустить фоновый сбор данных
        if config['monitoring']['auto_refresh'] and toyota_client:
            asyncio.create_task(collect_vehicle_data())
    except Exception as e:
        logger.error(f"Ошибка при запуске Toyota Dashboard Server: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await db.close()
    except Exception as e:
        logger.error(f"Ошибка при остановке Toyota Dashboard Server: {e}")

# Используем путь к базе данных из менеджера путей
db_path = paths.database_path
db = DatabaseManager(db_path)
toyota_client: Optional[MyT] = None
vehicle_vin = config.get('toyota', {}).get('vin', '')

app = FastAPI(title="Toyota Dashboard", version="1.0.0", lifespan=lifespan)

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
        # Проверить, что учетные данные настроены
        if not config.get('toyota', {}).get('username') or not config.get('toyota', {}).get('password'):
            logger.info("Toyota клиент не инициализирован - учетные данные не настроены")
            toyota_client = None
            return
            
        toyota_client = MyT(
            username=config['toyota']['username'],
            password=config['toyota']['password'],
            use_metric=config['dashboard'].get('units', 'metric') == 'metric'
        )
        logger.info("Toyota клиент успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации Toyota клиента: {e}")
        toyota_client = None

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
            if toyota_client and vehicle_vin:
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
                    
                    # Сохранить статус автомобиля в базу данных
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
                    
                    # Собрать данные о поездках за последние 7 дней
                    try:
                        from datetime import date, timedelta
                        end_date = date.today()
                        start_date = end_date - timedelta(days=7)
                        
                        # Получить поездки из Toyota API
                        trips = await target_vehicle.get_trips(start_date, end_date)
                        
                        if trips:
                            logger.info(f"Получено {len(trips)} поездок из Toyota API")
                            
                            # Сохранить поездки в базу данных
                            for trip in trips:
                                if trip.start_time and trip.end_time and trip.distance:
                                    # Проверить, есть ли уже эта поездка в базе
                                    existing_trip = await db.get_trip_by_time(trip.start_time)
                                    if not existing_trip:
                                        trip_data = {
                                            'start_time': trip.start_time,
                                            'end_time': trip.end_time,
                                            'distance_total': trip.distance or 0,
                                            'distance_electric': trip.ev_distance or 0,
                                            'fuel_consumed': trip.fuel_consumed or 0,
                                            'electricity_consumed': 0,  # Пока не доступно в API
                                            'start_latitude': trip.locations.start.lat if trip.locations and trip.locations.start else 0.0,
                                            'start_longitude': trip.locations.start.lon if trip.locations and trip.locations.start else 0.0,
                                            'end_latitude': trip.locations.end.lat if trip.locations and trip.locations.end else 0.0,
                                            'end_longitude': trip.locations.end.lon if trip.locations and trip.locations.end else 0.0
                                        }
                                        await db.save_trip(trip_data)
                                        logger.debug(f"Сохранена поездка: {trip.start_time} - {trip.distance} км")
                        else:
                            logger.debug("Новых поездок не найдено")
                            
                    except Exception as e:
                        logger.error(f"Ошибка сбора данных о поездках: {e}")
                    
                    logger.debug("Данные автомобиля и поездок обновлены")
                else:
                    logger.warning(f"Автомобиль с VIN {vehicle_vin} не найден")
            else:
                logger.debug("Toyota клиент или VIN не настроены, пропускаем сбор данных")
                
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
    if not config.get('toyota', {}).get('username') or not config.get('toyota', {}).get('password') or not config.get('toyota', {}).get('vin'):
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

@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page():
    """Страница уведомлений."""
    with open(paths.get_static_file('notifications.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    """Страница статистики."""
    with open(paths.get_static_file('stats.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/climate", response_class=HTMLResponse)
async def climate_page():
    """Страница климат-контроля."""
    with open(paths.get_static_file('climate.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/control", response_class=HTMLResponse)
async def control_page():
    """Страница управления автомобилем."""
    with open(paths.get_static_file('control.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    """Страница настроек."""
    with open(paths.get_static_file('settings.html'), 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/location-test", response_class=HTMLResponse)
async def location_test_page():
    """Страница тестирования местоположений."""
    with open(paths.get_static_file('location_test.html'), 'r', encoding='utf-8') as f:
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
        
        # Получаем данные о местоположении и ценах на топливо
        location_info = None
        if target_vehicle.location:
            location_info = await location_service.get_location_info(
                target_vehicle.location.latitude, 
                target_vehicle.location.longitude
            )
        
        return {
            "battery_level": target_vehicle.electric_status.battery_level if target_vehicle.electric_status else 0,
            "fuel_level": target_vehicle.dashboard.fuel_level if target_vehicle.dashboard else 0,
            "range_electric": target_vehicle.electric_status.ev_range if target_vehicle.electric_status else 0,
            "range_fuel": target_vehicle.dashboard.fuel_range if target_vehicle.dashboard else 0,
            "total_range": (target_vehicle.electric_status.ev_range if target_vehicle.electric_status else 0) + (target_vehicle.dashboard.fuel_range if target_vehicle.dashboard else 0),
            "charging_status": target_vehicle.electric_status.charging_status if target_vehicle.electric_status else "none",
            "remaining_charge_time": getattr(target_vehicle.electric_status, 'remaining_charge_time', None) if target_vehicle.electric_status else None,
            "location": location_info or {
                "latitude": target_vehicle.location.latitude if target_vehicle.location else 45.542026,
                "longitude": target_vehicle.location.longitude if target_vehicle.location else 13.713837,
                "city": "Копер",
                "country": "Slovenia",
                "address": "Копер, Словения",
                "fuel_price": 1.43,
                "fuel_currency": "€/л",
                "fuel_price_formatted": "1.43 €/л"
            },
            "locked": getattr(target_vehicle.lock_status, 'locked', True) if target_vehicle.lock_status else True,
            "engine_running": False,
            "climate_on": False,
            "temperature_inside": 0.0,
            "temperature_outside": 0.0,
            
            # Дополнительные данные
            "model_name": "Toyota C-HR - NG '24",
            "image_url": "https://dj3z27z47basa.cloudfront.net/3fd45119-ae71-4298-abd2-281907b01f73",
            "date_of_first_use": "2024-05-23",
            "vin": target_vehicle.vin,
            "alias": target_vehicle.alias,
            "odometer": target_vehicle.dashboard.odometer if target_vehicle.dashboard else 0,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        # Возвращаем fallback данные при ошибке
        return {
            "battery_level": 95,
            "fuel_level": 86,
            "range_electric": 74.1,
            "range_fuel": 459.0,
            "total_range": 533.1,
            "charging_status": "none",
            "remaining_charge_time": None,
            "location": {
                "latitude": 45.542026,
                "longitude": 13.713837,
                "city": "Копер",
                "country": "Slovenia",
                "address": "Копер, Словения",
                "fuel_price": 1.43,
                "fuel_currency": "€/л",
                "fuel_price_formatted": "1.43 €/л"
            },
            "locked": True,
            "engine_running": False,
            "climate_on": False,
            "temperature_inside": 0.0,
            "temperature_outside": 0.0,
            "model_name": "Toyota C-HR - NG '24",
            "image_url": "https://dj3z27z47basa.cloudfront.net/3fd45119-ae71-4298-abd2-281907b01f73",
            "date_of_first_use": "2024-05-23",
            "vin": "JTXXXXXXXXXXXXXXX",
            "alias": "My Toyota",
            "odometer": 38491,
            "last_updated": datetime.now().isoformat()
        }

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

@app.get("/api/vehicle/notifications")
async def get_vehicle_notifications():
    """Получить уведомления автомобиля."""
    try:
        target_vehicle = await get_vehicle()
        await target_vehicle.update()
        
        notifications = []
        if target_vehicle.notifications:
            for notif in target_vehicle.notifications[:20]:  # Последние 20 уведомлений
                # Переводим категории на русский
                category_translations = {
                    'ChargingAlert': 'Зарядка',
                    'VehicleStatusAlert': 'Статус автомобиля',
                    'RemoteCommand': 'Удаленная команда',
                    'UpdateSchedule': 'Расписание зарядки',
                    'ScheduledClimate': 'Климат-контроль',
                    'General': 'Общие'
                }
                
                category = category_translations.get(notif.category, notif.category)
                
                # Определяем тип уведомления
                notification_type = 'info'
                if hasattr(notif, 'icon_url') and notif.icon_url and 'critical' in notif.icon_url.lower():
                    notification_type = 'warning'
                elif notif.category in ['ChargingAlert']:
                    notification_type = 'success'
                
                notifications.append({
                    "id": getattr(notif, 'message_id', str(hash(notif.message))),
                    "title": category,
                    "message": notif.message,
                    "timestamp": getattr(notif, 'notification_date', datetime.now()).isoformat(),
                    "type": notification_type,
                    "icon_url": getattr(notif, 'icon_url', None),
                    "is_read": getattr(notif, 'is_read', False),
                    "status": getattr(notif, 'status', None)
                })
        
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Ошибка получения уведомлений: {e}")
        # Возвращаем fallback уведомления
        return {
            "notifications": [
                {
                    "id": "1",
                    "title": "Зарядка",
                    "message": "Toyota C-HR: Автомобиль полностью заряжен до установленного максимума.",
                    "timestamp": datetime.now().isoformat(),
                    "type": "success",
                    "icon_url": "https://assets.preprod.ctdevops.com/assets/notification/icons/general.png",
                    "is_read": False
                },
                {
                    "id": "2", 
                    "title": "Статус автомобиля",
                    "message": "Несколько предупреждений автомобиля, проверьте приложение для подробностей.",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "type": "warning",
                    "icon_url": "https://assets.preprod.ctdevops.com/assets/notification/icons/critical_alert.png",
                    "is_read": False
                }
            ]
        }

@app.get("/api/vehicle/location")
async def get_vehicle_location():
    """Получить информацию о местоположении и ценах на топливо."""
    try:
        target_vehicle = await get_vehicle()
        await target_vehicle.update()
        
        # Получаем координаты автомобиля
        if target_vehicle.location:
            latitude = target_vehicle.location.latitude
            longitude = target_vehicle.location.longitude
        else:
            # Fallback координаты (Копер, Словения)
            latitude = 45.542026
            longitude = 13.713837
        
        # Получаем информацию о местоположении и ценах на топливо
        location_info = await location_service.get_location_info(latitude, longitude)
        
        return location_info
        
    except Exception as e:
        logger.error(f"Ошибка получения местоположения: {e}")
        # Возвращаем fallback данные при ошибке
        return {
            "latitude": 45.542026,
            "longitude": 13.713837,
            "city": "Копер",
            "country": "Slovenia",
            "address": "Копер, Словения",
            "fuel_price": 1.43,
            "fuel_currency": "€/л",
            "fuel_price_formatted": "1.43 €/л"
        }

@app.get("/api/test/location")
async def test_location(lat: float, lon: float):
    """Тестовый endpoint для проверки определения местоположения."""
    try:
        location_info = await location_service.get_location_info(lat, lon)
        return location_info
    except Exception as e:
        logger.error(f"Ошибка тестирования местоположения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vehicle/climate/status")
async def get_climate_status():
    """Получить статус климат-контроля."""
    try:
        target_vehicle = await get_vehicle()
        
        # Попробуем получить статус климата
        climate_status = getattr(target_vehicle, 'climate_status', None)
        climate_settings = getattr(target_vehicle, 'climate_settings', None)
        
        return {
            "isOn": False,  # Заглушка, нужно найти правильное поле
            "temperature": 21,  # Заглушка
            "acOn": False,
            "heatOn": False,
            "frontDefrost": False,
            "rearDefrost": False
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса климата: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/climate/start")
async def start_climate(request: CommandRequest):
    """Запустить климат-контроль."""
    try:
        target_vehicle = await get_vehicle()
        
        # Отправить команду запуска климата
        result = await target_vehicle.post_command(
            command=CommandType.CLIMATE_START,
            duration=request.duration or 10,
            temperature=request.temperature or 21
        )
        
        return {"status": "success", "message": "Климат-контроль запущен"}
    except Exception as e:
        logger.error(f"Ошибка запуска климата: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vehicle/climate/stop")
async def stop_climate():
    """Остановить климат-контроль."""
    try:
        target_vehicle = await get_vehicle()
        
        # Отправить команду остановки климата
        result = await target_vehicle.post_command(CommandType.CLIMATE_STOP)
        
        return {"status": "success", "message": "Климат-контроль остановлен"}
    except Exception as e:
        logger.error(f"Ошибка остановки климата: {e}")
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
            "vehicle_info": f"{target_vehicle._vehicle_info.car_model_name} ({target_vehicle._vehicle_info.car_model_year})",
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
        
        # Получаем путь к файлу конфигурации
        config_file_path = paths.config_file
        logger.info(f"Попытка сохранения конфигурации в: {config_file_path}")
        
        # Проверяем возможность записи в директорию
        config_dir = os.path.dirname(config_file_path)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
                logger.info(f"Создана директория конфигурации: {config_dir}")
            except (OSError, PermissionError) as e:
                logger.error(f"Не удалось создать директорию конфигурации {config_dir}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Не удалось создать директорию конфигурации: {e}"
                )
        
        # Проверяем права на запись в директорию
        if not os.access(config_dir, os.W_OK):
            logger.error(f"Нет прав на запись в директорию: {config_dir}")
            raise HTTPException(
                status_code=500,
                detail=f"Нет прав на запись в директорию конфигурации: {config_dir}"
            )
        
        # Создаем резервную копию существующего файла конфигурации
        if os.path.exists(config_file_path):
            try:
                backup_path = f"{config_file_path}.backup"
                shutil.copy2(config_file_path, backup_path)
                logger.info(f"Создана резервная копия конфигурации: {backup_path}")
            except Exception as e:
                logger.warning(f"Не удалось создать резервную копию: {e}")
        
        # Сохранить в файл
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Конфигурация успешно сохранена в: {config_file_path}")
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка записи файла конфигурации {config_file_path}: {e}")
            
            # Пытаемся сохранить в альтернативное место
            fallback_path = os.path.join(os.path.expanduser("~"), '.config', 'toyota-dashboard', 'config.yaml')
            try:
                os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                with open(fallback_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                logger.info(f"Конфигурация сохранена в альтернативное место: {fallback_path}")
                
                # Обновляем путь в менеджере путей
                paths._user_config_dir = os.path.dirname(fallback_path)
                
            except Exception as fallback_error:
                logger.error(f"Не удалось сохранить конфигурацию в альтернативное место: {fallback_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Не удалось сохранить конфигурацию. Основная ошибка: {e}. Альтернативная ошибка: {fallback_error}"
                )
        
        # Обновить глобальные переменные
        vehicle_vin = request.vin
        
        # Переинициализировать Toyota клиент
        await init_toyota_client()
        
        # Если порт изменился, нужно перезапустить сервер
        current_port = config.get('server', {}).get('port', 2025)
        restart_required = request.port != current_port
        
        return {
            "success": True,
            "message": "Конфигурация сохранена успешно!",
            "config_path": config_file_path,
            "restart_required": restart_required
        }
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка сохранения конфигурации: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Неожиданная ошибка: {str(e)}"
            }
        )

@app.post("/api/collect-trips")
async def collect_trips():
    """Принудительно собрать данные о поездках из Toyota API."""
    try:
        if not toyota_client or not vehicle_vin:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Toyota клиент не инициализирован или VIN не настроен"
                }
            )
        
        # Получить автомобили
        await toyota_client.login()
        vehicles = await toyota_client.get_vehicles()
        
        # Найти нужный автомобиль по VIN
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
        
        # Собрать данные о поездках за последние 30 дней
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Получить поездки из Toyota API
        trips = await target_vehicle.get_trips(start_date, end_date)
        
        trips_saved = 0
        if trips:
            logger.info(f"Получено {len(trips)} поездок из Toyota API")
            
            # Сохранить поездки в базу данных
            for trip in trips:
                if trip.start_time and trip.end_time and trip.distance:
                    # Проверить, есть ли уже эта поездка в базе
                    existing_trip = await db.get_trip_by_time(trip.start_time)
                    if not existing_trip:
                        trip_data = {
                            'start_time': trip.start_time,
                            'end_time': trip.end_time,
                            'distance_total': trip.distance or 0,
                            'distance_electric': trip.ev_distance or 0,
                            'fuel_consumed': trip.fuel_consumed or 0,
                            'electricity_consumed': 0,  # Пока не доступно в API
                            'start_latitude': trip.locations.start.lat if trip.locations and trip.locations.start else 0.0,
                            'start_longitude': trip.locations.start.lon if trip.locations and trip.locations.start else 0.0,
                            'end_latitude': trip.locations.end.lat if trip.locations and trip.locations.end else 0.0,
                            'end_longitude': trip.locations.end.lon if trip.locations and trip.locations.end else 0.0
                        }
                        await db.save_trip(trip_data)
                        trips_saved += 1
                        logger.debug(f"Сохранена поездка: {trip.start_time} - {trip.distance} км")
        
        return {
            "success": True,
            "message": f"Собрано {len(trips) if trips else 0} поездок, сохранено {trips_saved} новых",
            "total_trips": len(trips) if trips else 0,
            "new_trips": trips_saved
        }
        
    except Exception as e:
        logger.error(f"Ошибка сбора данных о поездках: {e}")
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

@app.get("/api/statistics")
async def get_statistics():
    """Получить статистику поездок и использования автомобиля."""
    try:
        # Получить общую статистику из базы данных
        total_stats = await db.get_total_statistics()
        
        # Получить статистику за последние периоды
        stats_30d = await db.get_phev_statistics("30d")
        stats_7d = await db.get_phev_statistics("7d")
        
        return {
            "success": True,
            "total": {
                "distance": total_stats.get("total_distance", 0),
                "electric_percentage": total_stats.get("electric_percentage", 0),
                "fuel_consumed": total_stats.get("fuel_consumed", 0),
                "cost_savings": total_stats.get("cost_savings", 0)
            },
            "last_30_days": {
                "distance": stats_30d.get("distance", 0),
                "electric_percentage": stats_30d.get("electric_percentage", 0),
                "fuel_consumed": stats_30d.get("fuel_consumed", 0),
                "cost_savings": stats_30d.get("cost_savings", 0),
                "trips_count": stats_30d.get("trips_count", 0)
            },
            "last_7_days": {
                "distance": stats_7d.get("distance", 0),
                "electric_percentage": stats_7d.get("electric_percentage", 0),
                "fuel_consumed": stats_7d.get("fuel_consumed", 0),
                "cost_savings": stats_7d.get("cost_savings", 0),
                "trips_count": stats_7d.get("trips_count", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
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
        last_status = await db.get_latest_status()
        
        if last_status and last_status.get('latitude', 0) != 0 and last_status.get('longitude', 0) != 0:
            # Определить страну по координатам
            country_code = await fuel_price_service.get_country_by_coordinates(
                last_status['latitude'], last_status['longitude']
            )
            prices = await fuel_price_service.get_fuel_prices(
                latitude=last_status['latitude'], 
                longitude=last_status['longitude']
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

@app.get("/api/system/paths")
async def get_system_paths():
    """Получить информацию о системных путях для диагностики."""
    try:
        path_info = paths.get_info()
        
        # Добавляем дополнительную диагностическую информацию
        config_file_path = paths.config_file
        config_dir = os.path.dirname(config_file_path)
        
        diagnostic_info = {
            "paths": path_info,
            "config_file_status": {
                "path": config_file_path,
                "exists": os.path.exists(config_file_path),
                "readable": os.access(config_file_path, os.R_OK) if os.path.exists(config_file_path) else False,
                "writable": os.access(config_file_path, os.W_OK) if os.path.exists(config_file_path) else False,
            },
            "config_dir_status": {
                "path": config_dir,
                "exists": os.path.exists(config_dir),
                "readable": os.access(config_dir, os.R_OK) if os.path.exists(config_dir) else False,
                "writable": os.access(config_dir, os.W_OK) if os.path.exists(config_dir) else False,
            },
            "alternative_paths": []
        }
        
        # Проверяем альтернативные пути
        alternative_paths = [
            '/etc/toyota-dashboard/config.yaml',
            '/opt/toyota-dashboard/config.yaml',
            os.path.join(os.path.expanduser('~'), '.config', 'toyota-dashboard', 'config.yaml'),
            os.path.join(paths.app_dir, 'config.yaml')
        ]
        
        for alt_path in alternative_paths:
            alt_dir = os.path.dirname(alt_path)
            diagnostic_info["alternative_paths"].append({
                "path": alt_path,
                "exists": os.path.exists(alt_path),
                "readable": os.access(alt_path, os.R_OK) if os.path.exists(alt_path) else False,
                "writable": os.access(alt_path, os.W_OK) if os.path.exists(alt_path) else False,
                "dir_exists": os.path.exists(alt_dir),
                "dir_writable": os.access(alt_dir, os.W_OK) if os.path.exists(alt_dir) else False,
            })
        
        return diagnostic_info
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о путях: {e}")
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
        with open(paths.get_static_file('test_all.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Страница тестирования не найдена</h1>",
            status_code=404
        )

# Страница диагностики системы
@app.get("/diagnostics", response_class=HTMLResponse)
async def diagnostics_page():
    """Страница диагностики системы."""
    try:
        with open(os.path.join(APP_DIR, 'static', 'diagnostics.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Страница диагностики не найдена</h1>",
            status_code=404
        )

# Перенаправление с /statistics на /stats для совместимости
@app.get("/statistics", response_class=HTMLResponse)
async def statistics_redirect():
    """Перенаправление на страницу статистики."""
    return RedirectResponse(url="/stats", status_code=301)

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

# События приложения теперь обрабатываются через lifespan

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