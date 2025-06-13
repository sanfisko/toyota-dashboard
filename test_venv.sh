#!/bin/bash

# Тест виртуального окружения и команд Python

set -e

echo "🧪 Тестирование виртуального окружения..."

# Создаем тестовое виртуальное окружение
TEST_DIR="/tmp/test-venv-toyota"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Создание виртуального окружения..."
python3 -m venv test_venv

echo "🔧 Тестирование команд в виртуальном окружении..."

# Тестируем команду в том же формате, что и в install.sh
bash -c "
    source test_venv/bin/activate
    echo '✓ Виртуальное окружение активировано'
    python3 -c 'import sys; print(\"✓ Python версия:\", sys.version.split()[0])'
    python3 -c 'import sys; print(\"✓ Тест getattr:\", getattr(sys, \"version_info\", \"тест\"))'
"

echo "🧪 Тестирование проблемной команды..."
bash -c "
    source test_venv/bin/activate
    python3 -c 'import sys; print(\"✓ PyToyoda тест:\", getattr(sys, \"__version__\", \"локальная версия\"))'
" || echo "❌ Ошибка в команде"

echo "🧪 Тестирование с экранированными кавычками..."
bash -c "
    source test_venv/bin/activate
    python3 -c 'import sys; print(\"✓ PyToyoda тест:\", getattr(sys, \"__version__\", \"локальная версия\"))'
" || echo "❌ Ошибка в команде с экранированными кавычками"

# Очистка
cd /
rm -rf "$TEST_DIR"

echo "✅ Тестирование завершено"