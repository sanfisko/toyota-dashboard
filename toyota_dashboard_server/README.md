# 🚗📊 Toyota C-HR PHEV Dashboard Server

Персональный сервер для мониторинга и управления Toyota C-HR PHEV на Raspberry Pi с веб-интерфейсом для iPhone.

## 🎯 Возможности вашего Toyota C-HR PHEV

### 📊 Мониторинг (доступно через API)
- ✅ **Пробег**: день/неделя/месяц/год/всё время
- ✅ **Расход топлива**: детальная статистика и тренды  
- ✅ **Расход электричества**: эффективность PHEV режима
- ✅ **Местоположение**: текущее и история поездок
- ✅ **Состояние батареи**: уровень заряда HV батареи
- ✅ **Техническое состояние**: предупреждения и напоминания ТО
- ✅ **История поездок**: маршруты, время, эффективность

### 🎮 Управление (доступно для C-HR PHEV)
- ✅ **Замки**: блокировка/разблокировка дверей и багажника
- ✅ **Двигатель**: дистанционный запуск/остановка (предварительный прогрев)
- ✅ **Климат**: управление кондиционером и обогревом
- ✅ **Освещение**: включение фар и аварийной сигнализации
- ✅ **Поиск автомобиля**: звуковой сигнал и мигание фар
- ⚠️ **Окна**: управление стеклоподъемниками (зависит от комплектации)

### 📱 Веб-интерфейс для iPhone
- **Адаптивный дизайн** оптимизированный для iOS
- **PWA поддержка** - работает как нативное приложение
- **Темная/светлая тема** с автопереключением
- **Push-уведомления** о состоянии автомобиля
- **Офлайн-режим** с кэшированием данных

## 🛠️ Установка на Raspberry Pi

### Системные требования
```bash
# Рекомендуемая конфигурация
- Raspberry Pi 4B (4GB RAM)
- MicroSD карта 32GB+ (Class 10)
- Raspbian OS Lite (64-bit)
- Стабильное интернет-соединение
```

### Автоматическая установка
```bash
# Скачать и запустить установочный скрипт
curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/toyota_dashboard_server/install.sh | bash
```

### Ручная установка
```bash
# 1. Обновить систему
sudo apt update && sudo apt upgrade -y

# 2. Установить зависимости
sudo apt install python3-pip python3-venv nginx sqlite3 git -y

# 3. Клонировать проект
git clone https://github.com/sanfisko/toyota-dashboard.git
cd toyota-dashboard

# 4. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 5. Установить Python пакеты
pip install -r requirements.txt

# 6. Настроить конфигурацию
cp config.example.yaml config.yaml
nano config.yaml  # Добавить ваши Toyota credentials

# 7. Инициализировать базу данных
python manage.py init-db

# 8. Создать systemd сервис
sudo cp toyota-dashboard.service /etc/systemd/system/
sudo systemctl enable toyota-dashboard
sudo systemctl start toyota-dashboard
```

## ⚙️ Конфигурация

### config.yaml
```yaml
toyota:
  username: "your-email@example.com"  # Ваш Toyota Connected аккаунт
  password: "your-password"
  vin: "YOUR_VIN_NUMBER"             # VIN вашего C-HR PHEV
  region: "europe"

server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  secret_key: "generate-random-secret-key"

database:
  path: "data/toyota.db"
  backup_interval: 3600  # Резервное копирование каждый час

monitoring:
  data_collection_interval: 300  # Сбор данных каждые 5 минут
  trip_detection: true           # Автоматическое определение поездок
  auto_refresh: true            # Автообновление данных

phev_settings:
  charge_threshold_alert: 80    # Уведомление при заряде выше 80%
  ev_mode_preference: true      # Приоритет EV режима
  charging_schedule: "22:00"    # Время начала зарядки

notifications:
  low_battery_threshold: 20     # Уведомление при разряде ниже 20%
  low_fuel_threshold: 50        # Уведомление при топливе ниже 50км
  maintenance_alerts: true      # Напоминания о ТО
  trip_summaries: true         # Сводки поездок

dashboard:
  theme: "auto"                # auto, light, dark
  language: "ru"               # ru, en, de, fr
  timezone: "Europe/Moscow"
  units: "metric"              # metric, imperial
  currency: "RUB"              # Валюта для расчета стоимости
```

## 🌐 Доступ с iPhone

### В локальной сети
```
http://192.168.1.100:8000
```

### Настройка внешнего доступа
```bash
# Вариант 1: Cloudflare Tunnel (рекомендуется)
# Бесплатно и безопасно
cloudflared tunnel --url http://localhost:8000

# Вариант 2: ngrok
ngrok http 8000

# Вариант 3: Настройка роутера (Port Forwarding)
# Пробросить порт 8000 на внешний IP
```

### Установка как PWA на iPhone
1. Откройте сайт в Safari
2. Нажмите кнопку "Поделиться" 
3. Выберите "На экран Домой"
4. Приложение появится на рабочем столе

## 📊 API для разработчиков

### Статус автомобиля
```bash
# Общий статус
curl http://localhost:8000/api/vehicle/status

# Ответ:
{
  "battery_level": 85,
  "fuel_level": 45,
  "range_electric": 42,
  "range_fuel": 380,
  "location": {
    "latitude": 55.7558,
    "longitude": 37.6176
  },
  "locked": true,
  "engine_running": false,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Управление автомобилем
```bash
# Заблокировать двери
curl -X POST http://localhost:8000/api/vehicle/lock

# Запустить двигатель (прогрев)
curl -X POST http://localhost:8000/api/vehicle/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 10}'  # минуты

# Включить климат
curl -X POST http://localhost:8000/api/vehicle/climate \
  -H "Content-Type: application/json" \
  -d '{"temperature": 22, "mode": "heat"}'
```

### Статистика PHEV
```bash
# Эффективность за неделю
curl http://localhost:8000/api/stats/phev?period=week

# Ответ:
{
  "period": "week",
  "total_distance": 245.6,
  "electric_distance": 156.2,
  "fuel_distance": 89.4,
  "electric_percentage": 63.6,
  "fuel_consumption": 4.2,
  "electricity_consumption": 18.5,
  "co2_saved": 12.3,
  "cost_savings": 850
}
```

## 📱 Интерфейс для iPhone

### Главный экран
```
┌─────────────────────────┐
│  🚗 Toyota C-HR PHEV    │
├─────────────────────────┤
│  🔋 85%  ⛽ 45km        │
│  📍 Дом  🔒 Заблокирован │
├─────────────────────────┤
│  [🔓] [🚗] [❄️] [📍]    │
│  Открыть Запуск Климат Найти │
├─────────────────────────┤
│  📊 Сегодня:            │
│  🔋 25км (электро)      │
│  ⛽ 15км (бензин)       │
│  💰 Экономия: 120₽     │
└─────────────────────────┘
```

### Экран статистики
```
┌─────────────────────────┐
│  📊 Статистика          │
├─────────────────────────┤
│  [День] [Неделя] [Месяц] │
├─────────────────────────┤
│  📈 График расхода      │
│  ████████████████████   │
│                         │
│  🔋 Электро: 65%        │
│  ⛽ Бензин: 35%         │
│                         │
│  💰 Экономия: 2,450₽   │
│  🌱 CO₂ сэкономлено: 45кг│
└─────────────────────────┘
```

## 🔧 Обслуживание и мониторинг

### Системные логи
```bash
# Логи приложения
tail -f /var/log/toyota-dashboard/app.log

# Логи системного сервиса
journalctl -u toyota-dashboard -f

# Логи nginx
tail -f /var/log/nginx/access.log
```

### Мониторинг производительности
```bash
# Использование ресурсов
htop

# Место на диске
df -h

# Температура Raspberry Pi
vcgencmd measure_temp
```

### Автоматическое резервное копирование
```bash
# Добавить в crontab
crontab -e

# Резервное копирование каждый день в 2:00
0 2 * * * /home/pi/toyota-dashboard/scripts/backup.sh

# Очистка старых логов каждую неделю
0 0 * * 0 /home/pi/toyota-dashboard/scripts/cleanup.sh
```

## 🚨 Безопасность

### Базовая защита
```bash
# Изменить пароль пользователя pi
passwd

# Настроить файрвол
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # Dashboard

# Отключить SSH по паролю (использовать ключи)
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
```

### HTTPS в продакшене
```bash
# Установить certbot
sudo apt install certbot python3-certbot-nginx

# Получить SSL сертификат
sudo certbot --nginx -d your-domain.com

# Автообновление сертификата
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 🆘 Решение проблем

### Частые проблемы

**1. Не подключается к Toyota API**
```bash
# Проверить credentials
python3 -c "
from pytoyoda import MyT
client = MyT('your-email', 'your-password')
print('Подключение успешно!')
"

# Проверить интернет
ping google.com
```

**2. Сервер не запускается**
```bash
# Проверить порт
sudo netstat -tlnp | grep :8000

# Проверить логи
journalctl -u toyota-dashboard --no-pager

# Перезапустить сервис
sudo systemctl restart toyota-dashboard
```

**3. Не работает с iPhone**
```bash
# Найти IP адрес Raspberry Pi
hostname -I

# Проверить доступность с iPhone
# Открыть Safari и перейти на http://IP:8000
```

**4. Медленная работа**
```bash
# Проверить загрузку CPU
top

# Проверить память
free -h

# Оптимизировать базу данных
sqlite3 data/toyota.db "VACUUM;"
```

## 📈 Планы развития

### Ближайшие обновления
- 🔔 Push-уведомления через Telegram
- 📊 Экспорт данных в Excel/CSV
- 🗺️ Интеграция с картами
- 🏠 Интеграция с умным домом (Home Assistant)

### Долгосрочные планы
- 🤖 ИИ-анализ стиля вождения
- 📱 Нативное iOS приложение
- 🌐 Облачная синхронизация
- 👥 Семейные аккаунты

## 📞 Поддержка

### Сообщество
- **GitHub**: [Issues и обсуждения]
- **Telegram**: @toyota_chr_phev_ru
- **Discord**: Toyota Dashboard Community

### Коммерческая поддержка
- **Email**: support@toyota-dashboard.pro
- **Консультации**: от 2000₽/час
- **Установка под ключ**: от 15000₽

---

## 🎉 Заключение

Этот проект превратит ваш Toyota C-HR PHEV в полностью подключенный автомобиль с расширенными возможностями мониторинга и управления. 

**Основные преимущества:**
- 📊 Полный контроль над статистикой PHEV
- 🎮 Удобное управление с iPhone
- 💰 Экономия топлива через аналитику
- 🔒 Безопасность и приватность данных
- 🏠 Интеграция с умным домом

*Создано специально для российских владельцев Toyota C-HR PHEV* 🇷🇺