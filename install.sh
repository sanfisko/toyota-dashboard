#!/bin/bash

# Toyota Dashboard Server - Установочный скрипт для Raspberry Pi
# Автор: OpenHands AI
# Версия: 1.0.0

set -e  # Остановить при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Toyota Dashboard                          ║"
    echo "║              Установка на Raspberry Pi                      ║"
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

# Проверка системы
check_system() {
    print_step "Проверка системы..."
    
    # Проверка ОС
    if [[ ! -f /etc/os-release ]]; then
        print_error "Не удается определить операционную систему"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "raspbian" && "$ID" != "debian" && "$ID" != "ubuntu" ]]; then
        print_warning "Система не является Raspbian/Debian/Ubuntu. Продолжение на свой страх и риск."
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    if [[ "$ARCH" != "armv7l" && "$ARCH" != "aarch64" && "$ARCH" != "x86_64" ]]; then
        print_warning "Неподдерживаемая архитектура: $ARCH"
    fi
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не установлен"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
        print_error "Требуется Python 3.8 или выше. Установлен: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Система совместима"
}

# Обновление системы
update_system() {
    print_step "Обновление системы..."
    
    sudo apt update
    sudo apt upgrade -y
    
    print_success "Система обновлена"
}

# Установка зависимостей
install_dependencies() {
    print_step "Установка системных зависимостей..."
    
    sudo apt install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        nginx \
        sqlite3 \
        git \
        curl \
        wget \
        htop \
        logrotate \
        cron \
        bc
    
    print_success "Системные зависимости установлены"
}

# Создание пользователя
create_user() {
    print_step "Создание пользователя toyota..."
    
    if ! id "toyota" &>/dev/null; then
        sudo useradd -m -s /bin/bash toyota
        sudo usermod -aG sudo toyota
        print_success "Пользователь toyota создан"
    else
        print_info "Пользователь toyota уже существует"
    fi
}

# Создание директорий
create_directories() {
    print_step "Создание директорий..."
    
    sudo mkdir -p /opt/toyota-dashboard
    sudo mkdir -p /var/log/toyota-dashboard
    sudo mkdir -p /var/lib/toyota-dashboard/data
    sudo mkdir -p /var/lib/toyota-dashboard/backups
    
    sudo chown -R toyota:toyota /opt/toyota-dashboard
    sudo chown -R toyota:toyota /var/log/toyota-dashboard
    sudo chown -R toyota:toyota /var/lib/toyota-dashboard
    
    print_success "Директории созданы"
}

# Скачивание проекта
download_project() {
    print_step "Скачивание проекта..."
    
    cd /opt/toyota-dashboard
    
    # Если это локальная установка, копируем файлы
    if [[ -d "/workspace/pytoyoda" ]]; then
        sudo cp -r /workspace/pytoyoda/pytoyoda .
        sudo cp /workspace/pytoyoda/*.py .
        sudo cp /workspace/pytoyoda/*.sh .
        sudo cp /workspace/pytoyoda/*.yaml .
        sudo cp /workspace/pytoyoda/*.txt .
        sudo cp -r /workspace/pytoyoda/static .
    else
        # Скачиваем с GitHub
        sudo -u toyota git clone https://github.com/sanfisko/toyota-dashboard.git temp_repo
        sudo -u toyota cp temp_repo/*.py .
        sudo -u toyota cp temp_repo/*.sh .
        sudo -u toyota cp temp_repo/*.yaml .
        sudo -u toyota cp temp_repo/*.txt .
        sudo -u toyota cp -r temp_repo/static .
        sudo -u toyota cp -r temp_repo/pytoyoda .
        sudo -u toyota rm -rf temp_repo
    fi
    
    sudo chown -R toyota:toyota /opt/toyota-dashboard
    
    print_success "Проект скачан"
}

# Установка Python зависимостей
install_python_deps() {
    print_step "Установка Python зависимостей..."
    
    cd /opt/toyota-dashboard
    
    # Создание виртуального окружения
    sudo -u toyota python3 -m venv venv
    
    # Активация и установка зависимостей
    sudo -u toyota bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Установка PyToyoda
        if [[ -d 'pytoyoda' ]]; then
            pip install -e ./pytoyoda
        else
            pip install pytoyoda
        fi
    "
    
    print_success "Python зависимости установлены"
}

# Настройка конфигурации
setup_config() {
    print_step "Настройка конфигурации..."
    
    cd /opt/toyota-dashboard
    
    if [[ ! -f config.yaml ]]; then
        sudo -u toyota cp config.example.yaml config.yaml
        print_info "Создан файл config.yaml из примера"
        print_warning "ВАЖНО: Отредактируйте config.yaml и добавьте ваши Toyota credentials!"
    fi
    
    # Создание секретного ключа
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sudo -u toyota sed -i "s/your-secret-key-here/$SECRET_KEY/" config.yaml
    
    print_success "Конфигурация настроена"
}

# Инициализация базы данных
init_database() {
    print_step "Инициализация базы данных..."
    
    cd /opt/toyota-dashboard
    
    sudo -u toyota bash -c "
        source venv/bin/activate
        python3 -c '
import asyncio
from database import DatabaseManager

async def init_db():
    db = DatabaseManager(\"/var/lib/toyota-dashboard/data/toyota.db\")
    await db.init_database()
    await db.close()
    print(\"База данных инициализирована\")

asyncio.run(init_db())
        '
    "
    
    print_success "База данных инициализирована"
}

# Настройка systemd сервиса
setup_systemd() {
    print_step "Настройка systemd сервиса..."
    
    sudo tee /etc/systemd/system/toyota-dashboard.service > /dev/null <<EOF
[Unit]
Description=Toyota Dashboard Server
After=network.target

[Service]
Type=simple
User=toyota
Group=toyota
WorkingDirectory=/opt/toyota-dashboard
Environment=PATH=/opt/toyota-dashboard/venv/bin
ExecStart=/opt/toyota-dashboard/venv/bin/python app.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=toyota-dashboard

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/toyota-dashboard /var/log/toyota-dashboard

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable toyota-dashboard
    
    print_success "Systemd сервис настроен"
}

# Настройка nginx
setup_nginx() {
    print_step "Настройка nginx..."
    
    sudo tee /etc/nginx/sites-available/toyota-dashboard > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Статические файлы
    location /static/ {
        alias /opt/toyota-dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API и приложение
    location / {
        proxy_pass http://127.0.0.1:2025;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket поддержка
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/toyota-dashboard /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    sudo nginx -t
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    
    print_success "Nginx настроен"
}

# Настройка логирования
setup_logging() {
    print_step "Настройка логирования..."
    
    sudo tee /etc/logrotate.d/toyota-dashboard > /dev/null <<EOF
/var/log/toyota-dashboard/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 toyota toyota
    postrotate
        systemctl reload toyota-dashboard
    endscript
}
EOF
    
    print_success "Логирование настроено"
}

# Настройка резервного копирования
setup_backup() {
    print_step "Настройка резервного копирования..."
    
    sudo -u toyota tee /opt/toyota-dashboard/backup.sh > /dev/null <<'EOF'
#!/bin/bash

BACKUP_DIR="/var/lib/toyota-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/var/lib/toyota-dashboard/data/toyota.db"

# Создание резервной копии базы данных
if [[ -f "$DB_FILE" ]]; then
    sqlite3 "$DB_FILE" ".backup $BACKUP_DIR/toyota_$DATE.db"
    echo "Резервная копия создана: toyota_$DATE.db"
fi

# Удаление старых копий (старше 7 дней)
find "$BACKUP_DIR" -name "toyota_*.db" -mtime +7 -delete

# Архивирование конфигурации
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C /opt/toyota-dashboard config.yaml

echo "Резервное копирование завершено"
EOF
    
    sudo chmod +x /opt/toyota-dashboard/backup.sh
    
    # Добавление в crontab
    (sudo -u toyota crontab -l 2>/dev/null; echo "0 2 * * * /opt/toyota-dashboard/backup.sh") | sudo -u toyota crontab -
    
    print_success "Резервное копирование настроено"
}

# Настройка файрвола
setup_firewall() {
    print_step "Настройка файрвола..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        print_success "UFW файрвол настроен"
    else
        print_warning "UFW не установлен, пропускаем настройку файрвола"
    fi
}

# Запуск сервисов
start_services() {
    print_step "Запуск сервисов..."
    
    sudo systemctl start toyota-dashboard
    sudo systemctl start nginx
    
    # Проверка статуса
    sleep 5
    
    if sudo systemctl is-active --quiet toyota-dashboard; then
        print_success "Toyota Dashboard сервис запущен"
    else
        print_error "Ошибка запуска Toyota Dashboard сервиса"
        sudo journalctl -u toyota-dashboard --no-pager -n 20
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        print_success "Nginx запущен"
    else
        print_error "Ошибка запуска Nginx"
    fi
}

# Финальная информация
show_final_info() {
    print_success "Установка завершена!"
    echo
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    ВАЖНАЯ ИНФОРМАЦИЯ                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}1. Настройте конфигурацию:${NC}"
    echo "   sudo nano /opt/toyota-dashboard/config.yaml"
    echo
    echo -e "${YELLOW}2. Добавьте ваши Toyota credentials:${NC}"
    echo "   - username: ваш email от Toyota Connected"
    echo "   - password: ваш пароль"
    echo "   - vin: VIN номер вашего Toyota автомобиля"
    echo
    echo -e "${YELLOW}3. Перезапустите сервис после настройки:${NC}"
    echo "   sudo systemctl restart toyota-dashboard"
    echo
    echo -e "${YELLOW}4. Доступ к дашборду:${NC}"
    IP=$(hostname -I | awk '{print $1}')
    echo "   Локальная сеть: http://$IP (через nginx)"
    echo "   Прямой доступ: http://$IP:2025"
    echo "   Локально: http://localhost"
    echo "   Настройка: http://$IP/setup"
    echo
    echo -e "${YELLOW}5. Логи:${NC}"
    echo "   sudo journalctl -u toyota-dashboard -f"
    echo "   tail -f /var/log/toyota-dashboard/app.log"
    echo
    echo -e "${YELLOW}6. Управление сервисом:${NC}"
    echo "   sudo systemctl start|stop|restart|status toyota-dashboard"
    echo
    echo -e "${YELLOW}7. Удаление (если понадобится):${NC}"
    echo "   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh | sudo bash"
    echo
    echo -e "${GREEN}Установка завершена успешно! 🚗✨${NC}"
}

# Основная функция
main() {
    print_header
    
    # Проверка прав root
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
    
    # Подтверждение установки
    echo -e "${YELLOW}Этот скрипт установит Toyota Dashboard на ваш Raspberry Pi.${NC}"
    echo -e "${YELLOW}Продолжить? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Установка отменена"
        exit 0
    fi
    
    # Выполнение установки
    check_system
    update_system
    install_dependencies
    create_user
    create_directories
    download_project
    install_python_deps
    setup_config
    init_database
    setup_systemd
    setup_nginx
    setup_logging
    setup_backup
    setup_firewall
    start_services
    show_final_info
}

# Обработка ошибок
trap 'print_error "Установка прервана из-за ошибки на строке $LINENO"' ERR

# Запуск
main "$@"