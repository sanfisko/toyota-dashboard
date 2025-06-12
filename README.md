# 🚗 Toyota Dashboard

**Персональный сервер мониторинга и управления Toyota автомобилями для Raspberry Pi с веб-интерфейсом, оптимизированным для мобильных устройств**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Compatible-red.svg)](https://raspberrypi.org)

## 🌟 Возможности

### 🔋 Мониторинг автомобиля
- **Уровень топлива** - остаток топлива и запас хода
- **Состояние батареи** - заряд аккумулятора и электросистемы
- **Пробег** - одометр и статистика поездок
- **Техническое состояние** - диагностика и предупреждения

### 🚙 Удаленное управление
- **Замки** - блокировка/разблокировка дверей
- **Двигатель** - дистанционный запуск/остановка
- **Климат-контроль** - предварительный прогрев/охлаждение
- **Освещение** - управление фарами и сигналами

### 📊 Статистика и аналитика
- **История поездок** - детальная статистика использования
- **Графики потребления** - визуализация расхода топлива
- **Отчеты** - ежедневные, недельные, месячные сводки
- **Экспорт данных** - CSV, JSON форматы для анализа

### 📱 Современный веб-интерфейс
- **Адаптивный дизайн** - оптимизирован для всех устройств
- **PWA поддержка** - установка как мобильное приложение
- **Темная тема** - комфортное использование в любое время
- **Офлайн режим** - базовая функциональность без интернета

## 🚀 Быстрый старт

### Автоматическая установка на Raspberry Pi
```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh?$(date +%s)" | sudo bash
```

> **Примечание:** Скрипт запросит подтверждение перед началом установки.

### ⚠️ Решение проблем установки

**Проблемы с зависимостями или запуском сервиса:**
Если сервис не запускается, используйте:
```bash
# Исправить все проблемы одной командой
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_all_issues.sh" | sudo bash

# Или исправить отдельные проблемы:
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_dependencies.sh" | sudo bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_version_error.sh" | sudo bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_readonly_filesystem.sh" | sudo bash
```

**Ошибка "Read-only file system":**
Если видите ошибку "OSError: [Errno 30] Read-only file system", используйте:
```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_readonly_filesystem.sh" | sudo bash
```

**Ошибка "externally-managed-environment" (Python 3.11+):**
Если вы видите ошибку PEP 668, попробуйте:
```bash
# Обновите скрипт установки (может быть кеширование)
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh?$(date +%s)" | sudo bash

# Или установите вручную python3-full
sudo apt update && sudo apt install -y python3-full python3-venv
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh?$(date +%s)" | sudo bash
```

### Настройка через веб-интерфейс
1. Откройте `http://IP_RASPBERRY_PI/setup`
2. Введите ваши Toyota Connected Services credentials
3. Укажите VIN номер автомобиля
4. Нажмите "Проверить подключение"
5. Сохраните настройки

### Готово! 🎉
Откройте `http://IP_RASPBERRY_PI` и наслаждайтесь полным контролем над вашим Toyota!

## 📋 Системные требования

### Raspberry Pi
- **Модель**: Raspberry Pi 3B+ или новее
- **ОС**: Raspberry Pi OS (Debian 11+)
- **RAM**: Минимум 1GB
- **Место**: 2GB свободного места
- **Сеть**: Wi-Fi или Ethernet

### Toyota автомобиль
- **Подписка**: Toyota Connected Services
- **Совместимость**: Модели с поддержкой удаленного управления
- **Регион**: Поддерживаемые Toyota Connected регионы

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile/Web    │◄──►│  Raspberry Pi   │◄──►│  Toyota Cloud   │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • FastAPI       │    │ • Vehicle API   │
│ • Controls      │    │ • Database      │    │ • Telemetry     │
│ • Statistics    │    │ • Background    │    │ • Commands      │
│ • PWA App       │    │   Tasks         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Компоненты
- **FastAPI Backend** - REST API сервер
- **SQLite Database** - локальное хранение данных
- **Nginx Proxy** - веб-сервер и SSL терминация
- **Systemd Service** - автозапуск и мониторинг
- **PyToyoda Library** - интеграция с Toyota API

## 🔧 API Документация

### Основные эндпоинты
```http
GET  /api/vehicle/status     # Статус автомобиля
POST /api/vehicle/lock       # Заблокировать двери
POST /api/vehicle/unlock     # Разблокировать двери
POST /api/vehicle/start      # Запустить двигатель
POST /api/vehicle/stop       # Остановить двигатель
GET  /api/statistics/daily   # Дневная статистика
GET  /api/statistics/weekly  # Недельная статистика
```

### Веб-интерфейс
```http
GET  /              # Главная панель
GET  /setup         # Настройка credentials
GET  /statistics    # Страница статистики
GET  /settings      # Настройки системы
```

### Мониторинг
```http
GET  /health        # Проверка здоровья системы
GET  /metrics       # Метрики Prometheus
GET  /docs          # Swagger документация
```

## 🛠️ Ручная установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/sanfisko/toyota-dashboard.git
cd toyota-dashboard
```

### 2. Установка зависимостей
```bash
# Python зависимости
pip3 install -r requirements.txt

# Системные пакеты
sudo apt update
sudo apt install nginx sqlite3 python3-pip
```

### 3. Настройка конфигурации
```bash
# Копировать пример конфигурации
cp config.example.yaml config.yaml

# Отредактировать настройки
nano config.yaml
```

### 4. Запуск сервера
```bash
# Разработка
# Файлы уже в корне репозитория
python3 app.py

# Продакшн
uvicorn app:app --host 0.0.0.0 --port 2025
```

## 📱 Использование

### Добавление на главный экран мобильного устройства
1. Откройте сайт в браузере
2. Нажмите кнопку "Поделиться" (iOS) или меню (Android)
3. Выберите "На экран Домой" или "Добавить на главный экран"
4. Подтвердите добавление

### Основные функции
- **🔋 Мониторинг** - отслеживание состояния автомобиля
- **🚗 Управление** - дистанционные команды
- **📊 Статистика** - анализ использования
- **⚙️ Настройки** - конфигурация системы

### Горячие клавиши
- `R` - Обновить данные
- `L` - Заблокировать/разблокировать
- `S` - Запустить/остановить двигатель
- `C` - Управление климатом

## 🔒 Безопасность

### Рекомендации
- **Смените порт** по умолчанию (2025)
- **Настройте SSL** для внешнего доступа
- **Используйте VPN** для удаленного подключения
- **Регулярно обновляйте** систему

### Файрвол
```bash
# Разрешить только необходимые порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 2025  # Toyota Dashboard
sudo ufw enable
```

## 📊 Мониторинг

### Логи
```bash
# Логи приложения
sudo journalctl -u toyota-dashboard -f

# Логи файлов
tail -f /var/log/toyota-dashboard/app.log

# Логи nginx
tail -f /var/log/nginx/access.log
```

### Статус сервиса
```bash
# Проверить статус
sudo systemctl status toyota-dashboard

# Перезапустить
sudo systemctl restart toyota-dashboard

# Остановить/запустить
sudo systemctl stop toyota-dashboard
sudo systemctl start toyota-dashboard
```

## 🗑️ Удаление

### Полное удаление
```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh?$(date +%s)" | sudo bash
```

### Что удаляется
- ✅ Сервис и автозапуск
- ✅ Все файлы проекта
- ✅ Пользователь toyota
- ✅ Конфигурация nginx
- ✅ База данных и логи
- ✅ Правила файрвола

**Безопасно**: двойное подтверждение + отчет об удалении

## 🆘 Поддержка

### Сообщество
- 🐛 **[GitHub Issues](https://github.com/sanfisko/toyota-dashboard/issues)** - баги и предложения
- 💬 **Telegram**: @toyota_dashboard_support

### Документация
- 📖 **[Wiki](https://github.com/sanfisko/toyota-dashboard/wiki)** - подробные инструкции
- 🔧 **[API Docs](http://IP_RASPBERRY_PI/docs)** - Swagger документация
- 🎥 **[YouTube](https://youtube.com/@toyota-dashboard)** - видео инструкции

## 🤝 Участие в разработке

### Как помочь
1. **Fork** репозитория
2. **Создайте** feature branch
3. **Внесите** изменения
4. **Создайте** Pull Request

### Разработка
```bash
# Клонировать для разработки
git clone https://github.com/sanfisko/toyota-dashboard.git
cd toyota-dashboard

# Установить зависимости разработки
pip3 install -r requirements-dev.txt

# Запустить тесты
pytest

# Запустить линтер
flake8 *.py
```

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- **[PyToyoda](https://github.com/DurgNomis-drol/pytoyoda)** - библиотека для работы с Toyota API
- **[FastAPI](https://fastapi.tiangolo.com)** - современный веб-фреймворк
- **[Raspberry Pi Foundation](https://raspberrypi.org)** - за отличную платформу

---

**Сделано с ❤️ для сообщества Toyota** 🚗✨