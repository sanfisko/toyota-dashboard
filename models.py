"""
Модели данных для Toyota Dashboard
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum

class VehicleStatus(BaseModel):
    """Модель статуса автомобиля."""
    timestamp: datetime
    battery_level: Optional[int] = None
    fuel_level: Optional[int] = None
    range_electric: Optional[float] = None
    range_fuel: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locked: Optional[bool] = None
    engine_running: Optional[bool] = None
    climate_on: Optional[bool] = None
    temperature_inside: Optional[float] = None
    temperature_outside: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

class TripData(BaseModel):
    """Модель данных поездки."""
    start_time: datetime
    end_time: Optional[datetime] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    distance_total: Optional[float] = None
    distance_electric: Optional[float] = None
    distance_fuel: Optional[float] = None
    fuel_consumed: Optional[float] = None
    electricity_consumed: Optional[float] = None
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    efficiency_score: Optional[int] = None
    route_data: Optional[Dict[str, Any]] = None

class StatsPeriod(str, Enum):
    """Периоды для статистики."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"

class CommandStatus(str, Enum):
    """Статусы команд."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class NotificationType(str, Enum):
    """Типы уведомлений."""
    LOW_BATTERY = "low_battery"
    LOW_FUEL = "low_fuel"
    MAINTENANCE = "maintenance"
    TRIP_SUMMARY = "trip_summary"
    COMMAND_RESULT = "command_result"
    SYSTEM = "system"

class PHEVStats(BaseModel):
    """Статистика автомобиля."""
    period: str
    total_distance: float
    electric_distance: float
    fuel_distance: float
    electric_percentage: float
    fuel_consumption: float
    electricity_consumption: float
    co2_saved: float
    cost_savings: float
    avg_efficiency: float

class DashboardConfig(BaseModel):
    """Конфигурация дашборда."""
    theme: str = "auto"  # auto, light, dark
    language: str = "ru"
    timezone: str = "Europe/Moscow"
    units: str = "metric"  # metric, imperial
    currency: str = "RUB"
    
class ToyotaCredentials(BaseModel):
    """Учетные данные Toyota."""
    username: str
    password: str
    vin: str
    region: str = "europe"

class ServerConfig(BaseModel):
    """Конфигурация сервера."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    secret_key: str

class MonitoringConfig(BaseModel):
    """Конфигурация мониторинга."""
    data_collection_interval: int = 300  # секунды
    trip_detection: bool = True
    auto_refresh: bool = True

class NotificationConfig(BaseModel):
    """Конфигурация уведомлений."""
    low_battery_threshold: int = 20
    low_fuel_threshold: int = 50
    maintenance_alerts: bool = True
    trip_summaries: bool = True

class PHEVConfig(BaseModel):
    """Конфигурация автомобиля."""
    charge_threshold_alert: int = 80
    ev_mode_preference: bool = True
    charging_schedule: str = "22:00"

class AppConfig(BaseModel):
    """Общая конфигурация приложения."""
    toyota: ToyotaCredentials
    server: ServerConfig
    dashboard: DashboardConfig
    monitoring: MonitoringConfig
    notifications: NotificationConfig
    phev_settings: PHEVConfig

class LocationPoint(BaseModel):
    """Точка местоположения."""
    latitude: float
    longitude: float
    timestamp: datetime
    address: Optional[str] = None

class Route(BaseModel):
    """Маршрут поездки."""
    points: List[LocationPoint]
    total_distance: float
    duration: int  # секунды

class VehicleCommand(BaseModel):
    """Команда для автомобиля."""
    command_type: str
    parameters: Optional[Dict[str, Any]] = None
    timestamp: datetime
    status: CommandStatus = CommandStatus.PENDING

class Notification(BaseModel):
    """Уведомление."""
    id: Optional[int] = None
    timestamp: datetime
    type: NotificationType
    title: str
    message: str
    read: bool = False
    data: Optional[Dict[str, Any]] = None

class DailySummary(BaseModel):
    """Ежедневная сводка."""
    date: str
    trip_count: int
    total_distance: float
    electric_distance: float
    fuel_consumed: float
    electricity_consumed: float
    efficiency_score: Optional[int] = None

class WeeklySummary(BaseModel):
    """Недельная сводка."""
    week_start: str
    week_end: str
    daily_summaries: List[DailySummary]
    total_stats: PHEVStats

class ClimateSettings(BaseModel):
    """Настройки климата."""
    temperature: float
    mode: str  # heat, cool, auto
    fan_speed: int
    defrost: bool = False

class VehicleInfo(BaseModel):
    """Информация об автомобиле."""
    vin: str
    model: str = "Toyota"
    year: Optional[int] = None
    color: Optional[str] = None
    nickname: Optional[str] = None

class UserPreferences(BaseModel):
    """Пользовательские предпочтения."""
    dashboard_config: DashboardConfig
    notification_config: NotificationConfig
    phev_config: PHEVConfig
    vehicle_info: VehicleInfo

class APIResponse(BaseModel):
    """Стандартный ответ API."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[str] = None
    timestamp: datetime = datetime.now()

class HealthCheck(BaseModel):
    """Проверка состояния системы."""
    status: str
    timestamp: datetime
    toyota_client: bool
    database: bool
    uptime: int  # секунды
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class ChargingSession(BaseModel):
    """Сессия зарядки."""
    start_time: datetime
    end_time: Optional[datetime] = None
    start_battery_level: int
    end_battery_level: Optional[int] = None
    energy_added: Optional[float] = None  # кВт⋅ч
    charging_power: Optional[float] = None  # кВт
    cost: Optional[float] = None

class FuelSession(BaseModel):
    """Сессия заправки."""
    timestamp: datetime
    fuel_added: float  # литры
    cost: float
    fuel_price: float  # за литр
    location: Optional[str] = None

class MaintenanceRecord(BaseModel):
    """Запись о техобслуживании."""
    date: datetime
    type: str  # oil_change, inspection, repair
    description: str
    cost: Optional[float] = None
    mileage: int
    next_service_mileage: Optional[int] = None

class EcoScore(BaseModel):
    """Экологический рейтинг."""
    score: int  # 0-100
    electric_usage_percentage: float
    fuel_efficiency: float
    co2_emissions: float
    tips: List[str]

class TripAnalysis(BaseModel):
    """Анализ поездки."""
    trip_id: int
    eco_score: EcoScore
    efficiency_rating: str  # excellent, good, average, poor
    suggestions: List[str]
    comparison_to_average: Dict[str, float]