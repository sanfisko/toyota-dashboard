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
    
    # Удалить данные и резервные копии
    if [[ -d /var/lib/toyota-dashboard ]]; then
        rm -rf /var/lib/toyota-dashboard
        print_success "База данных и резервные копии удалены"
    fi
    
    # Удалить временные файлы
    if [[ -d /tmp/toyota-dashboard ]]; then
        rm -rf /tmp/toyota-dashboard
        print_success "Временные файлы удалены"
    fi
}

# Удаление конфигурации логирования и cron задач
remove_logging_and_cron() {
    print_info "Удаление конфигурации логирования и cron задач..."
    
    # Удалить конфигурацию logrotate
    if [[ -f /etc/logrotate.d/toyota-dashboard ]]; then
        rm -f /etc/logrotate.d/toyota-dashboard
        print_success "Конфигурация logrotate удалена"
    fi
    
    # Удалить cron задачи пользователя toyota
    if id "toyota" &>/dev/null; then
        sudo -u toyota crontab -r 2>/dev/null || true
        print_success "Cron задачи пользователя toyota удалены"
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
    
    # UFW правила (install.sh устанавливает правила для ssh, 80, 443)
    if command -v ufw >/dev/null 2>&1; then
        # Не удаляем SSH правило для безопасности
        ufw --force delete allow 80/tcp 2>/dev/null || true
        ufw --force delete allow 443/tcp 2>/dev/null || true
        print_success "UFW правила для Toyota Dashboard удалены (SSH правило сохранено)"
    fi
    
    # iptables правила (если UFW не используется)
    if ! command -v ufw >/dev/null 2>&1; then
        iptables -D INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
        iptables -D INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
        
        # Сохранить правила iptables
        if command -v iptables-save >/dev/null 2>&1; then
            # Создать директорию если не существует
            mkdir -p /etc/iptables 2>/dev/null || true
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        
        print_success "iptables правила удалены"
    fi
}

# Очистка пакетов (опционально)
cleanup_packages() {
    print_info "Очистка неиспользуемых пакетов..."
    
    # Автоочистка системных пакетов
    if command -v apt &> /dev/null; then
        apt autoremove -y >/dev/null 2>&1 || true
        apt autoclean >/dev/null 2>&1 || true
        print_success "Системные пакеты очищены"
    elif command -v yum &> /dev/null; then
        yum autoremove -y >/dev/null 2>&1 || true
        print_success "Системные пакеты очищены"
    elif command -v dnf &> /dev/null; then
        dnf autoremove -y >/dev/null 2>&1 || true
        print_success "Системные пакеты очищены"
    fi
    
    print_info "Примечание: Python пакеты не удаляются автоматически для безопасности"
    print_info "При необходимости удалите их вручную: pip3 uninstall <package_name>"
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
✅ Systemd сервис toyota-dashboard
✅ Файлы проекта (/opt/toyota-dashboard)
✅ База данных и резервные копии (/var/lib/toyota-dashboard)
✅ Логи (/var/log/toyota-dashboard)
✅ Пользователь toyota и его домашняя директория
✅ Конфигурация nginx (/etc/nginx/sites-available/toyota-dashboard)
✅ Конфигурация logrotate (/etc/logrotate.d/toyota-dashboard)
✅ Cron задачи пользователя toyota
✅ Правила файрвола (UFW/iptables)
✅ Временные файлы
✅ Автоочистка системных пакетов

Сохраненные компоненты (для безопасности):
⚠️  SSH правила файрвола
⚠️  Python пакеты (удалите вручную при необходимости)
⚠️  Системные пакеты (nginx, sqlite3, git и др.)

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
    echo "   • Systemd сервис toyota-dashboard"
    echo "   • Все файлы проекта (/opt/toyota-dashboard)"
    echo "   • База данных и резервные копии (/var/lib/toyota-dashboard)"
    echo "   • Логи (/var/log/toyota-dashboard)"
    echo "   • Пользователя toyota и его домашнюю директорию"
    echo "   • Конфигурацию nginx"
    echo "   • Конфигурацию logrotate"
    echo "   • Cron задачи пользователя toyota"
    echo "   • Правила файрвола (кроме SSH)"
    echo "   • Временные файлы"
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
            
            echo
            read -p "Введите 'DELETE' для подтверждения: " -r
            if [[ $REPLY != "DELETE" ]]; then
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
    
    # Удаление компонентов
    remove_service
    remove_nginx
    remove_logging_and_cron
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
    echo "   • Systemd сервис и автозапуск"
    echo "   • Все файлы проекта (/opt/toyota-dashboard)"
    echo "   • База данных и резервные копии (/var/lib/toyota-dashboard)"
    echo "   • Логи (/var/log/toyota-dashboard)"
    echo "   • Пользователь toyota и его домашняя директория"
    echo "   • Конфигурация nginx"
    echo "   • Конфигурация logrotate"
    echo "   • Cron задачи"
    echo "   • Правила файрвола (кроме SSH)"
    echo "   • Временные файлы"
    echo
    print_warning "Сохранено для безопасности:"
    echo "   • SSH правила файрвола"
    echo "   • Python пакеты (удалите вручную при необходимости)"
    echo "   • Системные пакеты (nginx, sqlite3, git и др.)"
    echo
    print_warning "Если вы хотите переустановить Toyota Dashboard:"
    echo "curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash"
    echo
    print_info "Спасибо за использование Toyota Dashboard!"
}

# Обработка сигналов
trap 'print_error "Удаление прервано пользователем"; exit 1' INT TERM

# Запуск
main "$@"