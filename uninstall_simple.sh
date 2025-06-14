#!/bin/bash

# Toyota Dashboard - Простой скрипт удаления
# Автор: OpenHands AI Assistant
# Версия: 2.0

echo "🗑️  Toyota Dashboard - Удаление"
echo "================================"

# Остановка приложения
echo "🛑 Остановка приложения..."
pkill -f "python app.py" || true
pkill -f "uvicorn" || true

# Остановка systemd сервиса
if command -v systemctl &> /dev/null && systemctl is-active --quiet toyota-dashboard; then
    echo "🛑 Остановка systemd сервиса..."
    sudo systemctl stop toyota-dashboard
    sudo systemctl disable toyota-dashboard
    sudo rm -f /etc/systemd/system/toyota-dashboard.service
    sudo systemctl daemon-reload
    echo "✅ Systemd сервис удален"
fi

# Удаление виртуального окружения
echo "📦 Удаление виртуального окружения..."
rm -rf venv
echo "✅ Виртуальное окружение удалено"

# Удаление кэша
echo "🗑️  Удаление кэша..."
rm -rf cache
rm -rf __pycache__
rm -rf .pytest_cache
echo "✅ Кэш удален"

# Удаление логов
read -p "Удалить логи? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf logs
    echo "✅ Логи удалены"
fi

# Удаление данных
read -p "Удалить базу данных и данные? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf data
    echo "✅ Данные удалены"
fi

# Удаление конфигурации
read -p "Удалить конфигурационный файл? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f config.yaml
    echo "✅ Конфигурация удалена"
fi

# Удаление скриптов
echo "🗑️  Удаление скриптов..."
rm -f start.sh
rm -f stop.sh
echo "✅ Скрипты удалены"

echo ""
echo "🎉 Удаление завершено!"
echo ""
echo "📋 Что осталось:"
echo "   - Основные файлы приложения (app.py, static/, etc.)"
echo "   - Файлы конфигурации (если не удалили)"
echo "   - База данных (если не удалили)"
echo ""
echo "Для полного удаления удалите всю папку проекта."