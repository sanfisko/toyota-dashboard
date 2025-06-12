# 🔒 Критичные исправления безопасности

## 1. Ограничение CORS (app.py)

### Текущий код (НЕБЕЗОПАСНО):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Открыт для всех доменов!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Исправленный код:
```python
# Получить разрешенные домены из конфигурации
allowed_origins = config.get('security', {}).get('allowed_origins', [
    "http://localhost:2025",
    "https://localhost:2025"
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## 2. Добавление базовой аутентификации

### Создать auth.py:
```python
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key-here"  # Из конфигурации
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Защитить API эндпоинты:
```python
from auth import get_current_user

@app.post("/api/vehicle/lock")
async def lock_vehicle(current_user: str = Depends(get_current_user)):
    # Только авторизованные пользователи могут управлять автомобилем
    pass

@app.post("/api/vehicle/start")
async def start_vehicle(current_user: str = Depends(get_current_user)):
    # Критичная операция требует авторизации
    pass
```

## 3. Обработка исключений

### Добавить в app.py:
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

### Безопасная загрузка конфигурации:
```python
def load_config() -> Dict:
    """Загрузить конфигурацию из файла."""
    config_path = os.getenv('CONFIG_PATH', 'config.yaml')
    
    try:
        if not os.path.exists(config_path):
            logger.error(f"Файл конфигурации {config_path} не найден!")
            # Создать базовую конфигурацию
            create_default_config(config_path)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Валидация обязательных полей
        required_fields = ['toyota.username', 'toyota.password', 'toyota.vin']
        for field in required_fields:
            if not get_nested_value(config, field):
                raise ValueError(f"Обязательное поле {field} не заполнено")
                
        return config
        
    except FileNotFoundError:
        logger.error(f"Файл {config_path} не найден!")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Ошибка в {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        raise

def get_nested_value(config: dict, key: str):
    """Получить значение по вложенному ключу (например, 'toyota.username')."""
    keys = key.split('.')
    value = config
    for k in keys:
        value = value.get(k, {})
    return value if value != {} else None
```

## 4. Валидация VIN номера

### Добавить в models.py:
```python
import re
from pydantic import validator

class ConfigRequest(BaseModel):
    username: str
    password: str
    vin: str
    region: str = "europe"
    port: int = 2025
    
    @validator('vin')
    def validate_vin(cls, v):
        # VIN должен быть 17 символов, без I, O, Q
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', v.upper()):
            raise ValueError('VIN должен содержать 17 символов (A-Z, 0-9, кроме I, O, Q)')
        return v.upper()
    
    @validator('username')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Username должен быть email адресом')
        return v
    
    @validator('port')
    def validate_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError('Порт должен быть в диапазоне 1024-65535')
        return v
```

## 5. Безопасное хранение паролей

### Обновить config.example.yaml:
```yaml
# Конфигурация Toyota Dashboard Server

# Настройки подключения к Toyota Connected Services
toyota:
  username: "your-email@example.com"
  password_hash: ""  # Хэш пароля (будет создан автоматически)
  vin: "YOUR_VIN_NUMBER"
  region: "europe"

# Настройки безопасности
security:
  secret_key: "your-secret-key-here"  # Для JWT токенов
  allowed_origins:
    - "http://localhost:2025"
    - "https://yourdomain.com"
  session_timeout_minutes: 30
  max_login_attempts: 5
```

### Обновить функцию сохранения конфигурации:
```python
from auth import get_password_hash

@app.post("/api/config/save")
async def save_config(request: ConfigRequest):
    try:
        # Хэшировать пароль перед сохранением
        password_hash = get_password_hash(request.password)
        
        # Обновить конфигурацию
        config['toyota']['username'] = request.username
        config['toyota']['password_hash'] = password_hash  # Сохранить хэш, не пароль
        config['toyota']['vin'] = request.vin
        config['toyota']['region'] = request.region
        config['server']['port'] = request.port
        
        # Удалить старый пароль в открытом виде (если есть)
        if 'password' in config['toyota']:
            del config['toyota']['password']
        
        # Сохранить в файл
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("Конфигурация сохранена")
        return {"status": "success", "message": "Конфигурация сохранена"}
        
    except Exception as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 6. Rate Limiting

### Добавить middleware для ограничения запросов:
```python
from collections import defaultdict
from time import time

# Простой rate limiter в памяти
request_counts = defaultdict(list)
RATE_LIMIT = 60  # запросов в минуту
RATE_WINDOW = 60  # секунд

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time()
    
    # Очистить старые запросы
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_WINDOW
    ]
    
    # Проверить лимит
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    # Добавить текущий запрос
    request_counts[client_ip].append(now)
    
    response = await call_next(request)
    return response
```

## 7. Логирование безопасности

### Добавить security логи:
```python
import logging

# Создать отдельный логгер для безопасности
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('logs/security.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)

@app.post("/api/auth/login")
async def login(credentials: LoginRequest, request: Request):
    client_ip = request.client.host
    
    try:
        # Попытка входа
        if verify_credentials(credentials.username, credentials.password):
            security_logger.info(f"Successful login: {credentials.username} from {client_ip}")
            return {"access_token": create_access_token({"sub": credentials.username})}
        else:
            security_logger.warning(f"Failed login attempt: {credentials.username} from {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        security_logger.error(f"Login error for {credentials.username} from {client_ip}: {e}")
        raise
```

## 8. Обновить install.sh для безопасности

### Добавить в install.sh:
```bash
# Создать безопасную конфигурацию
create_secure_config() {
    echo "🔒 Создание безопасной конфигурации..."
    
    # Генерировать случайный секретный ключ
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Создать конфигурацию с безопасными настройками
    sudo -u toyota tee /home/toyota/config.yaml > /dev/null <<EOF
security:
  secret_key: "$SECRET_KEY"
  allowed_origins:
    - "http://localhost:2025"
    - "http://$(hostname -I | awk '{print $1}'):2025"
  session_timeout_minutes: 30
  max_login_attempts: 5

toyota:
  username: ""
  password_hash: ""
  vin: ""
  region: "europe"

server:
  host: "0.0.0.0"
  port: 2025
  debug: false

database:
  path: "/home/toyota/toyota.db"

logging:
  level: "INFO"
  file: "/var/log/toyota-dashboard/app.log"
  security_file: "/var/log/toyota-dashboard/security.log"
EOF

    # Установить правильные права доступа
    sudo chmod 600 /home/toyota/config.yaml
    sudo chown toyota:toyota /home/toyota/config.yaml
}

# Настроить файрвол
setup_firewall() {
    echo "🔥 Настройка файрвола..."
    
    # Установить ufw если не установлен
    sudo apt install -y ufw
    
    # Сбросить правила
    sudo ufw --force reset
    
    # Базовые правила
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Разрешить SSH
    sudo ufw allow 22/tcp
    
    # Разрешить Toyota Dashboard
    sudo ufw allow 2025/tcp
    
    # Включить файрвол
    sudo ufw --force enable
    
    echo "✅ Файрвол настроен"
}
```

Эти исправления значительно повысят безопасность проекта и защитят от основных угроз.