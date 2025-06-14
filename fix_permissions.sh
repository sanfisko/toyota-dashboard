#!/bin/bash

# Скрипт для исправления прав доступа Toyota Dashboard
# Используется для исправления проблем с правами доступа на уже установленной системе

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
    print_error "Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Исправление прав доступа Toyota Dashboard      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

print_step "Проверка пользователя toyota..."

# Проверяем, существует ли пользователь toyota
if ! id "toyota" &>/dev/null; then
    print_error "Пользователь toyota не найден. Запустите install.sh сначала."
    exit 1
fi

print_success "Пользователь toyota найден"

print_step "Остановка сервиса toyota-dashboard..."
systemctl stop toyota-dashboard || true

print_step "Исправление прав доступа..."

# Убеждаемся, что домашняя директория существует и доступна
if [ ! -d "/home/toyota" ]; then
    mkdir -p /home/toyota
    print_info "Создана домашняя директория /home/toyota"
fi

# Устанавливаем правильные права доступа
chown toyota:toyota /home/toyota
chmod 755 /home/toyota
print_info "Установлены права доступа для /home/toyota"

# Создаем пользовательские директории для конфигурации
print_info "Создание пользовательских директорий..."
mkdir -p /home/toyota/.config/toyota-dashboard
mkdir -p /home/toyota/.local/share/toyota-dashboard
mkdir -p /home/toyota/.local/share/toyota-dashboard/logs
mkdir -p /home/toyota/.local/share/toyota-dashboard/backups
mkdir -p /home/toyota/.cache/toyota-dashboard

# Устанавливаем права доступа для всех директорий
chown -R toyota:toyota /home/toyota/.config
chown -R toyota:toyota /home/toyota/.local
chown -R toyota:toyota /home/toyota/.cache
chmod -R 755 /home/toyota/.config
chmod -R 755 /home/toyota/.local
chmod -R 755 /home/toyota/.cache

print_success "Пользовательские директории созданы и настроены"

# Проверяем системные директории
print_step "Проверка системных директорий..."

# Создаем системные директории если они не существуют
mkdir -p /opt/toyota-dashboard
mkdir -p /etc/toyota-dashboard
mkdir -p /var/lib/toyota-dashboard/data
mkdir -p /var/log/toyota-dashboard

# Устанавливаем права для системных директорий
chown -R toyota:toyota /var/lib/toyota-dashboard
chown -R toyota:toyota /var/log/toyota-dashboard
chmod -R 755 /var/lib/toyota-dashboard
chmod -R 755 /var/log/toyota-dashboard

print_success "Системные директории проверены"

# Копируем конфигурацию если она существует в системной директории
if [[ -f "/etc/toyota-dashboard/config.yaml" ]] && [[ ! -f "/home/toyota/.config/toyota-dashboard/config.yaml" ]]; then
    cp /etc/toyota-dashboard/config.yaml /home/toyota/.config/toyota-dashboard/config.yaml
    chown toyota:toyota /home/toyota/.config/toyota-dashboard/config.yaml
    print_info "Конфигурация скопирована в пользовательскую директорию"
fi

print_step "Запуск сервиса toyota-dashboard..."
systemctl start toyota-dashboard

print_step "Проверка статуса сервиса..."
sleep 3

if systemctl is-active --quiet toyota-dashboard; then
    print_success "Сервис toyota-dashboard запущен успешно"
else
    print_warning "Сервис toyota-dashboard не запущен. Проверьте логи:"
    print_info "sudo journalctl -u toyota-dashboard -f"
fi

echo
print_success "Исправление прав доступа завершено!"
echo
print_info "Для проверки статуса используйте:"
print_info "  sudo systemctl status toyota-dashboard"
print_info "  sudo journalctl -u toyota-dashboard -f"
echo