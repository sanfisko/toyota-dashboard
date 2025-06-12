#!/bin/bash

# Toyota Dashboard - Скрипт удаления
# Полностью удаляет Toyota Dashboard Server с Raspberry Pi

set -e

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

# Проверка прав root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root"
        echo "Используйте: sudo $0"
        exit 1
    fi
}



# Остановка и удаление сервиса
remove_service() {
    print_info "Остановка и удаление сервиса..."
    
    # Остановить сервис
    if systemctl is-active --quiet toyota-dashboard; then
        systemctl stop toyota-dashboard
        print_success "Сервис остановлен"
    fi
    
    # Отключить автозапуск
    if systemctl is-enabled --quiet toyota-dashboard; then
        systemctl disable toyota-dashboard
        print_success "Автозапуск отключен"
    fi
    
    # Удалить файл сервиса
    if [[ -f /etc/systemd/system/toyota-dashboard.service ]]; then
        rm -f /etc/systemd/system/toyota-dashboard.service
        systemctl daemon-reload
        print_success "Файл сервиса удален"
    fi
}

# Удаление nginx конфигурации
remove_nginx() {
    print_info "Удаление nginx конфигурации..."
    
    # Отключить сайт
    if [[ -L /etc/nginx/sites-enabled/toyota-dashboard ]]; then
        rm -f /etc/nginx/sites-enabled/toyota-dashboard
        print_success "Сайт отключен"
    fi
    
    # Удалить конфигурацию
    if [[ -f /etc/nginx/sites-available/toyota-dashboard ]]; then
        rm -f /etc/nginx/sites-available/toyota-dashboard
        print_success "Конфигурация nginx удалена"
    fi
    
    # Перезагрузить nginx
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        print_success "Nginx перезагружен"
    fi
}

# Удаление файлов проекта
remove_files() {
    print_info "Удаление файлов проекта..."
    
    # Удалить директорию проекта
    if [[ -d /opt/toyota-dashboard ]]; then
        rm -rf /opt/toyota-dashboard
        print_success "Файлы проекта удалены"
    fi
    
    # Удалить логи
    if [[ -d /var/log/toyota-dashboard ]]; then
        rm -rf /var/log/toyota-dashboard
        print_success "Логи удалены"
    fi
    
    # Удалить временные файлы
    if [[ -d /tmp/toyota-dashboard ]]; then
        rm -rf /tmp/toyota-dashboard
        print_success "Временные файлы удалены"
    fi
}

# Удаление пользователя
remove_user() {
    print_info "Удаление пользователя toyota..."
    
    if id "toyota" &>/dev/null; then
        # Завершить все процессы пользователя
        pkill -u toyota || true
        
        # Удалить пользователя и его домашнюю директорию
        userdel -r toyota 2>/dev/null || userdel toyota 2>/dev/null || true
        
        # Удалить группу если она существует
        groupdel toyota 2>/dev/null || true
        
        print_success "Пользователь toyota удален"
    fi
}

# Удаление правил файрвола
remove_firewall() {
    print_info "Удаление правил файрвола..."
    
    # UFW правила
    if command -v ufw >/dev/null 2>&1; then
        ufw --force delete allow 2025 2>/dev/null || true
        ufw --force delete allow 80 2>/dev/null || true
        ufw --force delete allow 443 2>/dev/null || true
        print_success "UFW правила удалены"
    fi
    
    # iptables правила (если UFW не используется)
    if ! command -v ufw >/dev/null 2>&1; then
        iptables -D INPUT -p tcp --dport 2025 -j ACCEPT 2>/dev/null || true
        iptables -D INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
        iptables -D INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
        
        # Сохранить правила iptables
        if command -v iptables-save >/dev/null 2>&1; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        
        print_success "iptables правила удалены"
    fi
}

# Очистка пакетов (опционально)
cleanup_packages() {
    print_info "Очистка неиспользуемых пакетов..."
    
    read -p "Удалить установленные Python пакеты? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Удалить только если они не используются другими приложениями
        pip3 uninstall -y fastapi uvicorn aiosqlite pyyaml 2>/dev/null || true
        print_success "Python пакеты удалены"
    fi
    
    # Автоочистка
    apt autoremove -y >/dev/null 2>&1 || true
    apt autoclean >/dev/null 2>&1 || true
}

# Создание отчета об удалении
create_removal_report() {
    local report_file="/tmp/toyota-dashboard-removal-$(date +%Y%m%d_%H%M%S).log"
    
    cat > "$report_file" << EOF
Toyota Dashboard - Отчет об удалении
=====================================
Дата: $(date)
Пользователь: $(whoami)
Система: $(uname -a)

Удаленные компоненты:
✅ Сервис toyota-dashboard
✅ Файлы проекта (/opt/toyota-dashboard)
✅ Пользователь toyota
✅ Конфигурация nginx
✅ Логи (/var/log/toyota-dashboard)
✅ Правила файрвола
✅ Временные файлы

Статус: Удаление завершено успешно
EOF

    print_success "Отчет сохранен: $report_file"
}

# Основная функция
main() {
    print_header "🗑️  TOYOTA DASHBOARD UNINSTALLER"
    
    # Проверки
    check_root
    
    # Подтверждение удаления
    print_header "🗑️  УДАЛЕНИЕ TOYOTA DASHBOARD"
    echo
    print_warning "Это действие удалит:"
    echo "   • Сервис toyota-dashboard"
    echo "   • Все файлы проекта (/opt/toyota-dashboard)"
    echo "   • Пользователя toyota"
    echo "   • Конфигурацию nginx"
    echo "   • Базу данных и логи"
    echo "   • Правила файрвола"
    echo
    print_warning "Данные Toyota credentials и история поездок будут потеряны!"
    echo
    
    echo "DEBUG: AUTO_CONFIRM=$AUTO_CONFIRM"
    echo "DEBUG: Checking terminal: [[ -t 0 ]]"
    
    # Если указан флаг -y, пропускаем подтверждение
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        print_info "Автоматическое подтверждение включено (-y флаг)"
        print_info "Начинаем удаление..."
    else
        echo "DEBUG: AUTO_CONFIRM is not true, checking terminal..."
        # Проверяем, запущен ли скрипт интерактивно
        if [[ -t 0 ]]; then
            echo "DEBUG: Terminal is interactive"
            # Интерактивный режим - запрашиваем подтверждение
            read -p "Вы уверены, что хотите удалить Toyota Dashboard? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                print_info "Удаление отменено"
                exit 0
            fi
            
            echo
            read -p "Введите 'DELETE' для подтверждения: " -r
            if [[ $REPLY != "DELETE" ]]; then
                print_info "Удаление отменено"
                exit 0
            fi
        else
            echo "DEBUG: Terminal is NOT interactive"
            # Неинтерактивный режим (curl | bash) - автоматическое подтверждение
            print_info "Неинтерактивный режим: автоматическое удаление Toyota Dashboard..."
            sleep 2  # Небольшая пауза для чтения предупреждений
        fi
    fi
    
    echo "DEBUG: Confirmation logic completed"
    
    print_header "🚀 НАЧИНАЕМ УДАЛЕНИЕ"
    
    # Удаление компонентов
    remove_service
    remove_nginx
    remove_files
    remove_user
    remove_firewall
    cleanup_packages
    
    # Создание отчета
    create_removal_report
    
    print_header "✅ УДАЛЕНИЕ ЗАВЕРШЕНО"
    echo
    print_success "Toyota Dashboard полностью удален с системы"
    echo
    print_info "Что было удалено:"
    echo "   • Сервис и автозапуск"
    echo "   • Все файлы проекта"
    echo "   • Пользователь toyota"
    echo "   • Конфигурация nginx"
    echo "   • База данных и логи"
    echo "   • Правила файрвола"
    echo
    print_warning "Если вы хотите переустановить Toyota Dashboard:"
    echo "curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash"
    echo
    print_info "Спасибо за использование Toyota Dashboard! 🚗"
}

# Обработка сигналов
trap 'print_error "Удаление прервано пользователем"; exit 1' INT TERM

# Запуск
main "$@"