#!/bin/bash

# Toyota Dashboard - Скрипт удаления (пользовательская установка)
# Удаляет Toyota Dashboard из домашней директории пользователя

set -e

# Определяем текущего пользователя и пути
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_HOME=$(eval echo "~$CURRENT_USER")
INSTALL_DIR="$CURRENT_HOME/toyota-dashboard"
CONFIG_DIR="$CURRENT_HOME/.config/toyota-dashboard"
DATA_DIR="$CURRENT_HOME/.local/share/toyota-dashboard"
CACHE_DIR="$CURRENT_HOME/.cache/toyota-dashboard"

# Параметры
AUTO_CONFIRM=false

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        -h|--help)
            echo "Использование: $0 [опции]"
            echo "Опции:"
            echo "  -y, --yes    Автоматическое подтверждение удаления"
            echo "  -h, --help   Показать эту справку"
            exit 0
            ;;
        *)
            echo "Неизвестная опция: $1"
            echo "Используйте -h для справки"
            exit 1
            ;;
    esac
done

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Основная функция
main() {
    print_header "🗑️  TOYOTA DASHBOARD UNINSTALLER (USER)"
    
    print_info "Пользователь: $CURRENT_USER"
    print_info "Домашняя директория: $CURRENT_HOME"
    print_info "Директория установки: $INSTALL_DIR"
    echo
    
    # Подтверждение удаления
    print_warning "Это действие удалит:"
    echo "   • Пользовательский systemd сервис toyota-dashboard"
    echo "   • Все файлы проекта ($INSTALL_DIR)"
    echo "   • Виртуальное окружение Python и все пакеты"
    echo "   • Конфигурацию ($CONFIG_DIR)"
    echo "   • Данные ($DATA_DIR)"
    echo "   • Кэш ($CACHE_DIR)"
    echo "   • Скрипты управления"
    echo
    print_warning "Данные Toyota credentials и история поездок будут потеряны!"
    echo
    
    # Если указан флаг -y, пропускаем подтверждение
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        print_info "Автоматическое подтверждение включено (-y флаг)"
        print_info "Начинаем удаление..."
    else
        # Проверяем, запущен ли скрипт интерактивно
        if [[ -t 0 ]]; then
            # Интерактивный режим - запрашиваем подтверждение
            read -p "Вы уверены, что хотите удалить Toyota Dashboard? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                print_info "Удаление отменено"
                exit 0
            fi
        else
            # Неинтерактивный режим (curl | bash) - автоматическое подтверждение
            print_info "Неинтерактивный режим: автоматическое удаление Toyota Dashboard..."
            sleep 2  # Небольшая пауза для чтения предупреждений
        fi
    fi
    
    print_header "🚀 НАЧИНАЕМ УДАЛЕНИЕ"
    
    # Проверка доступности systemd user session
    check_systemd_user() {
        if [[ -n "$SUDO_USER" ]]; then
            if ! sudo -u "$SUDO_USER" systemctl --user status >/dev/null 2>&1; then
                return 1
            fi
        else
            if ! systemctl --user status >/dev/null 2>&1; then
                return 1
            fi
        fi
        return 0
    }
    
    # Остановка и удаление сервиса
    print_info "Остановка сервиса..."
    
    # Проверяем наличие файла сервиса
    if [[ -f "$CURRENT_HOME/.config/systemd/user/toyota-dashboard.service" ]]; then
        # Проверяем доступность systemd
        if check_systemd_user; then
            if [[ -n "$SUDO_USER" ]]; then
                sudo -u "$SUDO_USER" systemctl --user stop toyota-dashboard.service 2>/dev/null || print_warning "Сервис не был запущен"
                sudo -u "$SUDO_USER" systemctl --user disable toyota-dashboard.service 2>/dev/null || print_warning "Сервис не был включен"
            else
                systemctl --user stop toyota-dashboard.service 2>/dev/null || print_warning "Сервис не был запущен"
                systemctl --user disable toyota-dashboard.service 2>/dev/null || print_warning "Сервис не был включен"
            fi
        else
            print_warning "Systemd user session недоступен, пропускаем остановку сервиса"
        fi
        
        # Удаление файла сервиса
        rm -f "$CURRENT_HOME/.config/systemd/user/toyota-dashboard.service"
        print_success "Файл сервиса удален"
        
        # Перезагрузка systemd (если доступен)
        if check_systemd_user; then
            if [[ -n "$SUDO_USER" ]]; then
                sudo -u "$SUDO_USER" systemctl --user daemon-reload 2>/dev/null || true
            else
                systemctl --user daemon-reload 2>/dev/null || true
            fi
        fi
    else
        print_info "Файл сервиса не найден"
    fi
    
    # Остановка процессов вручную (на случай если systemd недоступен)
    print_info "Остановка процессов Toyota Dashboard..."
    pkill -f "python.*app.py" 2>/dev/null || print_info "Процессы не найдены"
    pkill -f "start_service.sh" 2>/dev/null || true
    pkill -f "start.sh" 2>/dev/null || true
    
    # Удаление cron задач
    print_info "Удаление cron задач..."
    if [[ -n "$SUDO_USER" ]]; then
        if sudo -u "$SUDO_USER" crontab -l 2>/dev/null | grep -q "toyota-dashboard/autostart.sh"; then
            sudo -u "$SUDO_USER" crontab -l 2>/dev/null | grep -v "toyota-dashboard/autostart.sh" | sudo -u "$SUDO_USER" crontab -
            print_success "Cron задачи удалены"
        else
            print_info "Cron задачи не найдены"
        fi
    else
        if crontab -l 2>/dev/null | grep -q "toyota-dashboard/autostart.sh"; then
            crontab -l 2>/dev/null | grep -v "toyota-dashboard/autostart.sh" | crontab -
            print_success "Cron задачи удалены"
        else
            print_info "Cron задачи не найдены"
        fi
    fi
    
    # Удаление директорий
    for dir in "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$CACHE_DIR"; do
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            print_success "Удалена директория: $dir"
        else
            print_info "Директория не найдена: $dir"
        fi
    done
    
    # Удаление дополнительных файлов и логов
    print_info "Удаление дополнительных файлов..."
    
    # Удаляем логи из /tmp если есть
    rm -f /tmp/toyota-dashboard*.log 2>/dev/null || true
    
    # Удаляем возможные pid файлы
    rm -f /tmp/toyota-dashboard.pid 2>/dev/null || true
    
    # Удаляем директорию systemd если пустая
    if [[ -d "$CURRENT_HOME/.config/systemd/user" ]]; then
        if [[ -z "$(ls -A "$CURRENT_HOME/.config/systemd/user" 2>/dev/null)" ]]; then
            rmdir "$CURRENT_HOME/.config/systemd/user" 2>/dev/null || true
            print_info "Удалена пустая директория systemd/user"
        fi
    fi
    
    if [[ -d "$CURRENT_HOME/.config/systemd" ]]; then
        if [[ -z "$(ls -A "$CURRENT_HOME/.config/systemd" 2>/dev/null)" ]]; then
            rmdir "$CURRENT_HOME/.config/systemd" 2>/dev/null || true
            print_info "Удалена пустая директория systemd"
        fi
    fi
    
    # Отключение lingering (если был включен только для Toyota Dashboard)
    if command -v loginctl &> /dev/null && check_systemd_user; then
        # Проверяем, есть ли другие пользовательские сервисы
        if [[ -n "$SUDO_USER" ]]; then
            if ! sudo -u "$SUDO_USER" systemctl --user list-unit-files --state=enabled 2>/dev/null | grep -q "\.service"; then
                sudo loginctl disable-linger "$CURRENT_USER" 2>/dev/null || true
                print_info "Lingering отключен (нет других пользовательских сервисов)"
            else
                print_info "Lingering оставлен (есть другие пользовательские сервисы)"
            fi
        else
            if ! systemctl --user list-unit-files --state=enabled 2>/dev/null | grep -q "\.service"; then
                sudo loginctl disable-linger "$CURRENT_USER" 2>/dev/null || true
                print_info "Lingering отключен (нет других пользовательских сервисов)"
            else
                print_info "Lingering оставлен (есть другие пользовательские сервисы)"
            fi
        fi
    fi
    
    print_header "✅ УДАЛЕНИЕ ЗАВЕРШЕНО"
    echo
    print_success "Toyota Dashboard удален из пользовательской установки"
    echo
    print_info "Что было удалено:"
    echo "   • Пользовательский systemd сервис"
    echo "   • Все файлы проекта ($INSTALL_DIR)"
    echo "   • Виртуальное окружение Python и все пакеты"
    echo "   • Конфигурация ($CONFIG_DIR)"
    echo "   • Данные ($DATA_DIR)"
    echo "   • Кэш ($CACHE_DIR)"
    echo "   • Скрипты управления (start.sh, stop.sh, update.sh, start_service.sh)"
    echo "   • Cron задачи автозапуска"
    echo "   • Временные файлы и логи"
    echo
    print_info "Если вы хотите переустановить Toyota Dashboard:"
    echo "bash <(curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh)"
    echo
    print_info "Спасибо за использование Toyota Dashboard!"
}

# Обработка сигналов
trap 'print_error "Удаление прервано пользователем"; exit 1' INT TERM

# Запуск
main "$@"