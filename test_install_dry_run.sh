#!/bin/bash

# Тестовый запуск install.sh в режиме dry-run
# Проверяет основные функции без фактической установки

set -e

# Создаем временную директорию для тестирования
TEST_DIR="/tmp/toyota-dashboard-test-$$"
mkdir -p "$TEST_DIR"

# Копируем скрипт установки
cp install.sh "$TEST_DIR/install_test.sh"

# Модифицируем скрипт для тестового режима
sed -i 's/git clone https:\/\/github\.com\/sanfisko\/toyota-dashboard\.git/echo "DRY-RUN: git clone https:\/\/github.com\/sanfisko\/toyota-dashboard.git"/' "$TEST_DIR/install_test.sh"
sed -i 's/pip install/echo "DRY-RUN: pip install"/' "$TEST_DIR/install_test.sh"
sed -i 's/systemctl --user/echo "DRY-RUN: systemctl --user"/' "$TEST_DIR/install_test.sh"
sed -i 's/sudo loginctl/echo "DRY-RUN: sudo loginctl"/' "$TEST_DIR/install_test.sh"

echo "Запуск тестовой установки в режиме dry-run..."
echo "Тестовая директория: $TEST_DIR"
echo

# Запускаем тестовую установку
cd "$TEST_DIR"
bash install_test.sh -y

echo
echo "Тестовая установка завершена"
echo "Очистка тестовой директории..."
rm -rf "$TEST_DIR"
echo "Готово!"