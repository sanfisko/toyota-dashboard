#!/bin/bash

# Toyota Dashboard Server - Скрипт удаления пользовательской установки
# Автор: OpenHands AI
# Версия: 2.0.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                Toyota Dashboard Uninstaller                 ║"
    echo "║              Удаление пользовательской установки            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Получаем информацию о текущем пользователе
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)

# Пути для удаления
INSTALL_DIR="$CURRENT_HOME/toyota-dashboard"
CONFIG_DIR="$CURRENT_HOME/.config/toyota-dashboard"
DATA_DIR="$CURRENT_HOME/.local/share/toyota-dashboard"
CACHE_DIR="$CURRENT_HOME/.cache/toyota-dashboard"
SERVICE_FILE="$CURRENT_HOME/.config/systemd/user/toyota-dashboard.service"

main() {
    print_header
    
    print_info "Пользователь: $CURRENT_USER"
    print_info "Домашняя директория: $CURRENT_HOME"
    echo
    
    echo "Этот скрипт удалит Toyota Dashboard и все связанные файлы."
    echo "ВНИМАНИЕ: Все данные, включая базу данных и логи, будут удалены!"
    echo
    read -p "Вы уверены, что хотите продолжить? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Удаление отменено"
        exit 0
    fi
    
    # Остановка и удаление сервиса
    print_step "Остановка и удаление systemd сервиса..."
    
    if systemctl --user is-active toyota-dashboard.service >/dev/null 2>&1; then
        systemctl --user stop toyota-dashboard.service
        print_info "Сервис остановлен"
    fi
    
    if systemctl --user is-enabled toyota-dashboard.service >/dev/null 2>&1; then
        systemctl --user disable toyota-dashboard.service
        print_info "Автозапуск отключен"
    fi
    
    if [[ -f "$SERVICE_FILE" ]]; then
        rm -f "$SERVICE_FILE"
        print_info "Файл сервиса удален"
    fi
    
    systemctl --user daemon-reload 2>/dev/null || true
    print_success "Systemd сервис удален"
    
    # Остановка процессов
    print_step "Остановка процессов..."
    pkill -f "python.*app.py" 2>/dev/null || print_info "Процессы не найдены"
    print_success "Процессы остановлены"
    
    # Удаление файлов
    print_step "Удаление файлов..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        print_info "Удалена директория установки: $INSTALL_DIR"
    fi
    
    if [[ -d "$CACHE_DIR" ]]; then
        rm -rf "$CACHE_DIR"
        print_info "Удалена директория кэша: $CACHE_DIR"
    fi
    
    # Спрашиваем про конфигурацию и данные
    echo
    read -p "Удалить конфигурацию? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ -d "$CONFIG_DIR" ]]; then
            rm -rf "$CONFIG_DIR"
            print_info "Удалена директория конфигурации: $CONFIG_DIR"
        fi
    else
        print_info "Конфигурация сохранена: $CONFIG_DIR"
    fi
    
    echo
    read -p "Удалить данные и логи? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ -d "$DATA_DIR" ]]; then
            rm -rf "$DATA_DIR"
            print_info "Удалена директория данных: $DATA_DIR"
        fi
    else
        print_info "Данные и логи сохранены: $DATA_DIR"
    fi
    
    print_success "Файлы удалены"
    
    # Очистка временных файлов
    print_step "Очистка временных файлов..."
    rm -rf "/tmp/toyota-dashboard" 2>/dev/null || true
    print_success "Временные файлы очищены"
    
    print_success "Удаление завершено!"
    
    echo
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    УДАЛЕНИЕ ЗАВЕРШЕНО                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
    echo "Toyota Dashboard успешно удален с вашей системы."
    echo
    if [[ -d "$CONFIG_DIR" ]] || [[ -d "$DATA_DIR" ]]; then
        echo "Сохраненные файлы:"
        [[ -d "$CONFIG_DIR" ]] && echo "  Конфигурация: $CONFIG_DIR"
        [[ -d "$DATA_DIR" ]] && echo "  Данные и логи: $DATA_DIR"
        echo
        echo "Для полного удаления выполните:"
        [[ -d "$CONFIG_DIR" ]] && echo "  rm -rf $CONFIG_DIR"
        [[ -d "$DATA_DIR" ]] && echo "  rm -rf $DATA_DIR"
    fi
    echo
    echo "Спасибо за использование Toyota Dashboard! 👋"
}

# Запускаем основную функцию
main "$@"