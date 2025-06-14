#!/bin/bash

# Toyota Dashboard - Простой установочный скрипт
# Автор: OpenHands AI Assistant
# Версия: 2.0

set -e

echo "🚗 Toyota Dashboard - Установка"
echo "================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION найден"

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден. Установите pip."
    exit 1
fi

echo "✅ pip найден"

# Создание виртуального окружения
echo "📦 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "⬆️  Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install fastapi uvicorn aiosqlite pyyaml aiohttp

# Установка pytoyoda
echo "🔧 Установка pytoyoda..."
pip install "pytoyoda@git+https://github.com/pytoyoda/pytoyoda@main"

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p data
mkdir -p logs
mkdir -p cache

# Создание конфигурационного файла
if [ ! -f "config.yaml" ]; then
    echo "⚙️  Создание конфигурационного файла..."
    cat > config.yaml << EOF
# Toyota Dashboard Configuration
app:
  name: "Toyota Dashboard"
  version: "2.0"
  debug: false
  host: "0.0.0.0"
  port: 8000

database:
  path: "data/toyota_dashboard.db"

cache:
  directory: "cache"

logging:
  level: "INFO"
  file: "logs/app.log"

toyota:
  # Учетные данные будут запрашиваться при первом запуске
  username: ""
  password: ""
  vin: ""
  
features:
  real_time_updates: true
  location_tracking: true
  fuel_price_tracking: true
  notifications: true
  climate_control: true
  remote_commands: true
EOF
    echo "✅ Конфигурационный файл создан"
else
    echo "✅ Конфигурационный файл уже существует"
fi

# Создание скрипта запуска
echo "🚀 Создание скрипта запуска..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python app.py
EOF

chmod +x start.sh
echo "✅ Скрипт запуска создан"

# Создание скрипта остановки
echo "🛑 Создание скрипта остановки..."
cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f "python app.py"
echo "Toyota Dashboard остановлен"
EOF

chmod +x stop.sh
echo "✅ Скрипт остановки создан"

# Проверка установки
echo "🔍 Проверка установки..."
if python -c "import fastapi, uvicorn, aiosqlite, yaml, aiohttp, pytoyoda" 2>/dev/null; then
    echo "✅ Все зависимости установлены корректно"
else
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi

echo ""
echo "🎉 Установка завершена успешно!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте config.yaml и укажите ваши учетные данные Toyota"
echo "2. Запустите приложение: ./start.sh"
echo "3. Откройте браузер: http://localhost:8000"
echo ""
echo "🔧 Дополнительные команды:"
echo "   Запуск: ./start.sh"
echo "   Остановка: ./stop.sh"
echo "   Удаление: ./uninstall.sh"
echo ""
echo "📱 Для использования как PWA на iPhone:"
echo "   1. Откройте Safari на iPhone"
echo "   2. Перейдите на http://your-server-ip:8000"
echo "   3. Нажмите 'Поделиться' → 'На экран Домой'"
echo ""
echo "🆘 Поддержка: https://github.com/Harvardtabby2dv/toyota-dashboard"