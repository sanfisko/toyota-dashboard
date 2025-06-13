#!/bin/bash

# Скрипт для копирования изменений в репозиторий sanfisko/toyota-dashboard

echo "🔄 Копирование изменений в репозиторий sanfisko/toyota-dashboard..."

# Создать временную директорию
TEMP_DIR="/tmp/toyota-dashboard-copy"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

echo "📥 Клонирование репозитория sanfisko/toyota-dashboard..."
git clone https://github.com/sanfisko/toyota-dashboard.git "$TEMP_DIR"

if [ ! -d "$TEMP_DIR" ]; then
    echo "❌ Ошибка клонирования репозитория"
    exit 1
fi

echo "📋 Копирование файлов..."

# Копировать основные файлы
cp -f install.sh "$TEMP_DIR/"
cp -f uninstall.sh "$TEMP_DIR/"
cp -f app.py "$TEMP_DIR/"
cp -f toyota_client.py "$TEMP_DIR/"
cp -f paths.py "$TEMP_DIR/"
cp -f setup_config.py "$TEMP_DIR/"
cp -f check_paths.py "$TEMP_DIR/"
cp -f requirements.txt "$TEMP_DIR/"

# Копировать статические файлы
cp -f static/test_all.html "$TEMP_DIR/static/"

# Копировать pytoyoda
cp -rf pytoyoda "$TEMP_DIR/"

cd "$TEMP_DIR"

echo "📝 Коммит изменений..."
git add .
git commit -m "Обновление с исправлениями и новыми функциями

- Исправлена система путей и конфигурации
- Добавлена полная тестовая страница /test-all
- Исправлены проблемы установки зависимостей
- Обновлен uninstall.sh для полного удаления
- Исправлена синтаксическая ошибка в install.sh
- Интегрирован реальный Toyota API через pytoyoda"

echo "🚀 Пуш в репозиторий..."
git push origin main

echo "✅ Готово! Изменения скопированы в sanfisko/toyota-dashboard"

# Очистка
rm -rf "$TEMP_DIR"