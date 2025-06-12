# Архитектурные улучшения для PyToyoda

## 1. Улучшение обработки ошибок

### 1.1 Иерархия исключений
```python
# pytoyoda/exceptions.py

class ToyotaBaseError(Exception):
    """Base exception for all Toyota-related errors."""
    
    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class ToyotaApiError(ToyotaBaseError):
    """Base class for API-related errors."""
    pass

class ToyotaAuthenticationError(ToyotaApiError):
    """Authentication-related errors."""
    pass

class ToyotaLoginError(ToyotaAuthenticationError):
    """Login failure errors."""
    pass

class ToyotaTokenError(ToyotaAuthenticationError):
    """Token-related errors."""
    pass

class ToyotaNetworkError(ToyotaApiError):
    """Network-related errors."""
    pass

class ToyotaTimeoutError(ToyotaNetworkError):
    """Request timeout errors."""
    pass

class ToyotaRateLimitError(ToyotaApiError):
    """Rate limiting errors."""
    pass

class ToyotaValidationError(ToyotaBaseError):
    """Input validation errors."""
    pass

class ToyotaVehicleError(ToyotaApiError):
    """Vehicle-specific errors."""
    pass

class ToyotaActionNotSupportedError(ToyotaVehicleError):
    """Action not supported on vehicle."""
    pass
```

### 1.2 Контекстный обработчик ошибок
```python
# pytoyoda/error_handler.py

import httpx
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar('T')

class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def map_http_error(response: httpx.Response) -> ToyotaApiError:
        """Map HTTP errors to specific Toyota exceptions."""
        status_code = response.status_code
        
        if status_code == 401:
            return ToyotaAuthenticationError("Authentication failed", "AUTH_FAILED")
        elif status_code == 403:
            return ToyotaAuthenticationError("Access forbidden", "ACCESS_DENIED")
        elif status_code == 429:
            return ToyotaRateLimitError("Rate limit exceeded", "RATE_LIMIT")
        elif status_code >= 500:
            return ToyotaInternalError("Toyota server error", "SERVER_ERROR")
        else:
            return ToyotaApiError(f"API error: {status_code}", "API_ERROR")
    
    @staticmethod
    def handle_network_error(error: Exception) -> ToyotaNetworkError:
        """Handle network-related errors."""
        if isinstance(error, httpx.TimeoutException):
            return ToyotaTimeoutError("Request timeout", "TIMEOUT")
        elif isinstance(error, httpx.ConnectError):
            return ToyotaNetworkError("Connection failed", "CONNECTION_ERROR")
        else:
            return ToyotaNetworkError(f"Network error: {error}", "NETWORK_ERROR")

def handle_api_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for handling API errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            raise ErrorHandler.map_http_error(e.response) from e
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            raise ErrorHandler.handle_network_error(e) from e
        except Exception as e:
            # Логировать неожиданные ошибки
            logger.exception("Unexpected error in {}", func.__name__)
            raise ToyotaInternalError(f"Unexpected error: {e}") from e
    
    return wrapper
```

## 2. Retry механизм

### 2.1 Конфигурируемый retry
```python
# pytoyoda/retry.py

import asyncio
import random
from typing import Callable, TypeVar, Any
from functools import wraps
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        ToyotaNetworkError,
        ToyotaTimeoutError,
        ToyotaInternalError,
    )

class RetryHandler:
    """Handle retry logic with exponential backoff."""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Проверить, можно ли повторить
                if not isinstance(e, self.config.retryable_exceptions):
                    raise
                
                # Последняя попытка
                if attempt == self.config.max_attempts - 1:
                    raise
                
                # Вычислить задержку
                delay = self._calculate_delay(attempt)
                logger.warning(
                    "Attempt {} failed, retrying in {:.2f}s: {}",
                    attempt + 1,
                    delay,
                    str(e)
                )
                
                await asyncio.sleep(delay)
        
        # Не должно дойти сюда, но на всякий случай
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Добавить случайность ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

def retry(config: RetryConfig = None):
    """Decorator for adding retry logic to functions."""
    retry_handler = RetryHandler(config)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator
```

## 3. Кэширование

### 3.1 Многоуровневое кэширование
```python
# pytoyoda/cache.py

import asyncio
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    data: T
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() > self.expires_at
    
    def access(self) -> T:
        """Mark entry as accessed and return data."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.data

class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> None:
        """Set cache entry."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete cache entry."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

class MemoryCache(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry
            elif entry:
                # Удалить просроченную запись
                del self._cache[key]
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> None:
        async with self._lock:
            # Проверить размер кэша
            if len(self._cache) >= self.max_size:
                await self._evict_lru()
            
            self._cache[key] = entry
    
    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Найти запись с наименьшим временем последнего доступа
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or datetime.min
        )
        del self._cache[lru_key]

class CacheManager:
    """Manage caching with TTL and invalidation."""
    
    def __init__(self, backend: CacheBackend = None):
        self.backend = backend or MemoryCache()
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[..., T],
        ttl: timedelta,
        *args,
        **kwargs
    ) -> T:
        """Get from cache or set using factory function."""
        entry = await self.backend.get(key)
        
        if entry:
            return entry.access()
        
        # Создать новую запись
        data = await factory(*args, **kwargs)
        entry = CacheEntry(
            data=data,
            created_at=datetime.now(),
            expires_at=datetime.now() + ttl
        )
        
        await self.backend.set(key, entry)
        return data
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        # Для простоты, очищаем весь кэш
        # В реальной реализации можно использовать более сложную логику
        await self.backend.clear()

# Декоратор для кэширования
def cached(ttl: timedelta, key_prefix: str = None):
    """Decorator for caching function results."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache_manager = CacheManager()
        prefix = key_prefix or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            key = cache_manager._make_key(prefix, *args, **kwargs)
            return await cache_manager.get_or_set(key, func, ttl, *args, **kwargs)
        
        return wrapper
    return decorator
```

## 4. Конфигурация и настройки

### 4.1 Централизованная конфигурация
```python
# pytoyoda/config.py

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class ApiConfig:
    """API configuration."""
    base_url: str = "https://ctpa-oneapi.tceu-ctp-prd.toyotaconnectedeurope.io"
    api_key: str = field(default_factory=lambda: os.getenv("TOYOTA_API_KEY", ""))
    client_version: str = field(default_factory=lambda: os.getenv("TOYOTA_CLIENT_VERSION", "2.14.0"))
    timeout: int = field(default_factory=lambda: int(os.getenv("TOYOTA_TIMEOUT", "60")))

@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = field(default_factory=lambda: os.getenv("TOYOTA_CACHE_ENABLED", "true").lower() == "true")
    ttl_seconds: int = field(default_factory=lambda: int(os.getenv("TOYOTA_CACHE_TTL", "300")))
    max_size: int = field(default_factory=lambda: int(os.getenv("TOYOTA_CACHE_MAX_SIZE", "1000")))

@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = field(default_factory=lambda: int(os.getenv("TOYOTA_RETRY_MAX_ATTEMPTS", "3")))
    base_delay: float = field(default_factory=lambda: float(os.getenv("TOYOTA_RETRY_BASE_DELAY", "1.0")))
    max_delay: float = field(default_factory=lambda: float(os.getenv("TOYOTA_RETRY_MAX_DELAY", "60.0")))

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = field(default_factory=lambda: os.getenv("TOYOTA_LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv("TOYOTA_LOG_FORMAT", "json"))
    file_path: Optional[str] = field(default_factory=lambda: os.getenv("TOYOTA_LOG_FILE"))

@dataclass
class ToyotaConfig:
    """Main configuration class."""
    api: ApiConfig = field(default_factory=ApiConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'ToyotaConfig':
        """Load configuration from file."""
        # Реализация загрузки из YAML/JSON файла
        pass
    
    @classmethod
    def from_env(cls) -> 'ToyotaConfig':
        """Load configuration from environment variables."""
        return cls()

# Глобальная конфигурация
config = ToyotaConfig.from_env()
```

## 5. Метрики и мониторинг

### 5.1 Система метрик
```python
# pytoyoda/metrics.py

import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Metric:
    """Base metric class."""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collect and manage metrics."""
    
    def __init__(self):
        self._counters: Counter = Counter()
        self._gauges: Dict[str, float] = {}
        self._histograms: defaultdict = defaultdict(list)
        self._timers: defaultdict = defaultdict(list)
    
    def increment(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record histogram value."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
    
    def time_operation(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, labels)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> List[Metric]:
        """Get all collected metrics."""
        metrics = []
        
        # Counters
        for key, value in self._counters.items():
            name, labels = self._parse_key(key)
            metrics.append(Metric(name, MetricType.COUNTER, value, labels=labels))
        
        # Gauges
        for key, value in self._gauges.items():
            name, labels = self._parse_key(key)
            metrics.append(Metric(name, MetricType.GAUGE, value, labels=labels))
        
        return metrics
    
    def _parse_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse metric key back to name and labels."""
        if '{' not in key:
            return key, {}
        
        name, label_part = key.split('{', 1)
        label_part = label_part.rstrip('}')
        
        labels = {}
        if label_part:
            for pair in label_part.split(','):
                k, v = pair.split('=', 1)
                labels[k] = v
        
        return name, labels

class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_histogram(f"{self.name}_duration", duration, self.labels)
            
            # Также записать как счетчик
            status = "error" if exc_type else "success"
            labels_with_status = {**self.labels, "status": status}
            self.collector.increment(f"{self.name}_total", labels=labels_with_status)

# Глобальный коллектор метрик
metrics = MetricsCollector()

# Декоратор для автоматического сбора метрик
def track_metrics(operation_name: str = None):
    """Decorator for tracking function metrics."""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with metrics.time_operation(name):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## 6. Улучшенная архитектура клиента

### 6.1 Модульная архитектура
```python
# pytoyoda/client_v2.py

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

@runtime_checkable
class AuthProvider(Protocol):
    """Authentication provider interface."""
    
    async def authenticate(self) -> str:
        """Authenticate and return access token."""
        ...
    
    async def refresh_token(self) -> str:
        """Refresh access token."""
        ...
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        ...

@runtime_checkable
class CacheProvider(Protocol):
    """Cache provider interface."""
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl: timedelta = None) -> None:
        """Set value in cache."""
        ...

class ToyotaClientV2:
    """Improved Toyota client with modular architecture."""
    
    def __init__(
        self,
        auth_provider: AuthProvider,
        cache_provider: CacheProvider = None,
        config: ToyotaConfig = None,
    ):
        self.auth = auth_provider
        self.cache = cache_provider
        self.config = config or ToyotaConfig.from_env()
        self._api = ApiClient(self.auth, self.config)
    
    async def get_vehicles(self) -> List[Vehicle]:
        """Get vehicles with caching."""
        cache_key = f"vehicles:{self.auth.username}"
        
        if self.cache:
            cached_vehicles = await self.cache.get(cache_key)
            if cached_vehicles:
                return cached_vehicles
        
        vehicles = await self._api.get_vehicles()
        
        if self.cache:
            await self.cache.set(
                cache_key, 
                vehicles, 
                ttl=timedelta(seconds=self.config.cache.ttl_seconds)
            )
        
        return vehicles
```

Эти архитектурные улучшения сделают библиотеку более надежной, масштабируемой и удобной в сопровождении.