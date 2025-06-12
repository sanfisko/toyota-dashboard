# Предложения по улучшению безопасности

## 1. Вынос API ключей в переменные окружения

### Текущая проблема
В файле `pytoyoda/controller.py` API ключи захардкожены:

```python
headers = {
    "x-api-key": "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF",
    "API_KEY": "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF",
    # ...
}
```

### Рекомендуемое решение

#### 1.1 Создать файл с константами окружения
```python
# pytoyoda/config.py
import os

# API Configuration
TOYOTA_API_KEY = os.getenv(
    "TOYOTA_API_KEY", 
    "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF"  # fallback для обратной совместимости
)

# Client Configuration  
CLIENT_VERSION = os.getenv("TOYOTA_CLIENT_VERSION", "2.14.0")

# Timeout Configuration
DEFAULT_TIMEOUT = int(os.getenv("TOYOTA_TIMEOUT", "60"))
```

#### 1.2 Обновить controller.py
```python
from pytoyoda.config import TOYOTA_API_KEY, DEFAULT_TIMEOUT

class Controller:
    def __init__(self, username: str, password: str, timeout: int = DEFAULT_TIMEOUT):
        # ...
        
    def _prepare_headers(self, vin: str | None = None, additional_headers: dict[str, Any] | None = None) -> dict[str, str]:
        headers = {
            "x-api-key": TOYOTA_API_KEY,
            "API_KEY": TOYOTA_API_KEY,
            # ...
        }
```

#### 1.3 Создать .env.example
```bash
# Toyota API Configuration
TOYOTA_API_KEY=your_api_key_here
TOYOTA_CLIENT_VERSION=2.14.0
TOYOTA_TIMEOUT=60

# Logging Configuration
LOG_LEVEL=INFO
```

## 2. Улучшение валидации входных данных

### 2.1 Валидация email
```python
import re
from typing import Pattern

EMAIL_PATTERN: Pattern[str] = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

class MyT:
    def __init__(self, username: str, password: str, use_metric: bool = True):
        if not self._is_valid_email(username):
            raise ToyotaInvalidUsernameError(
                "Invalid email format. Must be a valid email address."
            )
        # ...
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format."""
        return bool(EMAIL_PATTERN.match(email))
```

### 2.2 Валидация VIN
```python
VIN_PATTERN: Pattern[str] = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

def validate_vin(vin: str) -> bool:
    """Validate Vehicle Identification Number format."""
    return bool(VIN_PATTERN.match(vin.upper()))
```

## 3. Безопасное хранение токенов

### 3.1 Шифрование токенов в кэше
```python
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureTokenCache:
    def __init__(self, password: str):
        self._cipher = self._create_cipher(password)
        self._cache: dict[str, bytes] = {}
    
    def _create_cipher(self, password: str) -> Fernet:
        """Create encryption cipher from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'toyota_salt',  # В продакшене использовать случайную соль
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def store_token(self, username: str, token_info: TokenInfo) -> None:
        """Store encrypted token."""
        token_data = token_info.model_dump_json()
        encrypted_data = self._cipher.encrypt(token_data.encode())
        self._cache[username] = encrypted_data
    
    def get_token(self, username: str) -> TokenInfo | None:
        """Retrieve and decrypt token."""
        if username not in self._cache:
            return None
        
        try:
            encrypted_data = self._cache[username]
            decrypted_data = self._cipher.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            return TokenInfo(**token_data)
        except Exception:
            # Токен поврежден или неверный пароль
            del self._cache[username]
            return None
```

## 4. Rate Limiting и защита от злоупотреблений

### 4.1 Простой rate limiter
```python
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window)
        self.requests: defaultdict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier."""
        async with self._lock:
            now = datetime.now()
            # Очистить старые запросы
            cutoff = now - self.time_window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]
            
            # Проверить лимит
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # Добавить текущий запрос
            self.requests[identifier].append(now)
            return True

# Использование в Controller
class Controller:
    def __init__(self, username: str, password: str, timeout: int = 60):
        # ...
        self._rate_limiter = RateLimiter(max_requests=100, time_window=3600)
    
    async def request_json(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        if not await self._rate_limiter.is_allowed(self._username):
            raise ToyotaApiError("Rate limit exceeded. Please try again later.")
        
        return await super().request_json(method, endpoint, **kwargs)
```

## 5. Логирование безопасности

### 5.1 Безопасное логирование
```python
import re
from loguru import logger

# Паттерны для маскировки чувствительных данных
SENSITIVE_PATTERNS = [
    (re.compile(r'("password":\s*")[^"]*(")', re.IGNORECASE), r'\1***\2'),
    (re.compile(r'("access_token":\s*")[^"]*(")', re.IGNORECASE), r'\1***\2'),
    (re.compile(r'("refresh_token":\s*")[^"]*(")', re.IGNORECASE), r'\1***\2'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE), r'\1***'),
]

def sanitize_log_data(data: str) -> str:
    """Remove sensitive information from log data."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        data = pattern.sub(replacement, data)
    return data

# Кастомный логгер
class SecureLogger:
    @staticmethod
    def log_api_request(method: str, url: str, headers: dict, body: dict | None = None):
        """Log API request with sensitive data masked."""
        safe_headers = {k: "***" if k.lower() in ["authorization", "x-api-key"] else v 
                       for k, v in headers.items()}
        safe_body = sanitize_log_data(str(body)) if body else None
        
        logger.info(
            "API Request",
            method=method,
            url=url,
            headers=safe_headers,
            body=safe_body
        )
```

## 6. Проверка SSL сертификатов

### 6.1 Строгая проверка SSL
```python
import ssl
import httpx

class Controller:
    async def _get_http_client(self) -> AsyncGenerator:
        """Context manager for HTTP client with strict SSL verification."""
        # Создать строгий SSL контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        async with httpx.AsyncClient(
            timeout=self._timeout,
            verify=ssl_context,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        ) as client:
            yield client
```

## 7. Защита от инъекций

### 7.1 Валидация параметров URL
```python
from urllib.parse import quote

def safe_url_param(value: str) -> str:
    """Safely encode URL parameter."""
    return quote(str(value), safe='')

# В API методах
async def get_trips(self, vin: str, from_date: date, to_date: date, **kwargs) -> TripsResponseModel:
    # Валидация VIN
    if not validate_vin(vin):
        raise ToyotaApiError("Invalid VIN format")
    
    # Безопасное формирование URL
    endpoint = VEHICLE_TRIPS_ENDPOINT.format(
        from_date=safe_url_param(str(from_date)),
        to_date=safe_url_param(str(to_date)),
        # ...
    )
```

## 8. Мониторинг безопасности

### 8.1 Аудит безопасности
```python
from datetime import datetime
from enum import Enum

class SecurityEvent(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    TOKEN_REFRESH = "token_refresh"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_REQUEST = "invalid_request"

class SecurityAuditor:
    def __init__(self):
        self.events: list[dict] = []
    
    def log_event(self, event: SecurityEvent, username: str, details: dict | None = None):
        """Log security event."""
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event": event.value,
            "username": username,
            "details": details or {}
        }
        self.events.append(event_data)
        
        # Логировать критические события
        if event in [SecurityEvent.LOGIN_FAILURE, SecurityEvent.RATE_LIMIT_EXCEEDED]:
            logger.warning("Security event", **event_data)
```

## Заключение

Эти улучшения значительно повысят безопасность библиотеки:

1. **Конфиденциальность**: API ключи не будут храниться в коде
2. **Целостность**: Валидация входных данных предотвратит ошибки
3. **Доступность**: Rate limiting защитит от злоупотреблений
4. **Аудит**: Логирование поможет отслеживать проблемы безопасности
5. **Шифрование**: Токены будут храниться в зашифрованном виде

Рекомендуется внедрять эти улучшения поэтапно, начиная с наиболее критичных (вынос API ключей и валидация входных данных).