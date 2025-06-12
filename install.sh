#!/bin/bash

# Toyota Dashboard Server - Установочный скрипт для Raspberry Pi
# Автор: OpenHands AI
# Версия: 1.0.0
#
# Использование:
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash -s -- -y
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash -s -- --fix-deps
#
# Флаги:
#   -y, --yes                    Автоматическое подтверждение без интерактивного запроса
#   --fix-deps, --fix-dependencies   Исправление зависимостей в уже установленной системе

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

# Проверка и установка Python
check_and_install_python() {
    print_step "Проверка Python..."
    
    # Проверяем, установлен ли Python 3
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 не найден. Устанавливаем..."
        
        # Определяем пакетный менеджер и устанавливаем Python
        if command -v apt &> /dev/null; then
            apt update
            apt install -y python3 python3-pip python3-venv python3-dev
        elif command -v yum &> /dev/null; then
            yum install -y python3 python3-pip python3-venv python3-devel
        elif command -v dnf &> /dev/null; then
            dnf install -y python3 python3-pip python3-venv python3-devel
        elif command -v pacman &> /dev/null; then
            pacman -S --noconfirm python python-pip python-virtualenv
        else
            print_error "Неподдерживаемый пакетный менеджер. Установите Python 3.8+ вручную."
            exit 1
        fi
        
        # Проверяем установку
        if ! command -v python3 &> /dev/null; then
            print_error "Не удалось установить Python 3"
            exit 1
        fi
        
        print_success "Python 3 успешно установлен"
    fi
    
    # Получаем версию Python
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
    
    print_success "Python $PYTHON_VERSION найден"
    
    # Проверяем версию Python (требуется 3.8+)
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        print_warning "Установлен Python $PYTHON_VERSION, но требуется 3.8+. Попытка обновления..."
        
        # Пытаемся установить более новую версию
        if command -v apt &> /dev/null; then
            # Для Debian/Ubuntu пытаемся установить из deadsnakes PPA
            apt update
            apt install -y software-properties-common
            add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
            apt update
            
            # Пытаемся установить Python 3.11
            if apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev 2>/dev/null; then
                # Создаем симлинк для python3
                update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
                print_success "Python 3.11 установлен и настроен"
            else
                print_error "Не удалось обновить Python до версии 3.8+. Текущая версия: $PYTHON_VERSION"
                print_error "Пожалуйста, обновите Python вручную до версии 3.8 или выше"
                exit 1
            fi
        else
            print_error "Требуется Python 3.8 или выше. Установлен: $PYTHON_VERSION"
            print_error "Пожалуйста, обновите Python вручную"
            exit 1
        fi
        
        # Перепроверяем версию после обновления
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
        
        if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
            print_error "Обновление Python не удалось. Версия: $PYTHON_VERSION"
            exit 1
        fi
        
        print_success "Python успешно обновлен до версии $PYTHON_VERSION"
    fi
    
    # Проверяем наличие pip
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 не найден. Устанавливаем..."
        
        if command -v apt &> /dev/null; then
            apt install -y python3-pip
        elif command -v yum &> /dev/null; then
            yum install -y python3-pip
        elif command -v dnf &> /dev/null; then
            dnf install -y python3-pip
        else
            # Устанавливаем pip через get-pip.py
            curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 - --break-system-packages 2>/dev/null || \
            curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 - --user
        fi
        
        print_success "pip3 установлен"
    fi
    
    # Пропускаем обновление системного pip из-за PEP 668
    # pip будет обновлен позже в виртуальном окружении
    print_success "Системный pip найден (будет обновлен в виртуальном окружении)"
    
    print_success "Python $PYTHON_VERSION готов к использованию"
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
    
    # Проверка и установка Python
    check_and_install_python
    
    print_success "Система совместима"
}

# Обновление системы
update_system() {
    print_step "Обновление системы..."
    
    # Определяем пакетный менеджер и обновляем систему
    if command -v apt &> /dev/null; then
        apt update
        apt upgrade -y
    elif command -v yum &> /dev/null; then
        yum update -y
    elif command -v dnf &> /dev/null; then
        dnf update -y
    elif command -v pacman &> /dev/null; then
        pacman -Syu --noconfirm
    else
        print_warning "Неизвестный пакетный менеджер. Пропускаем обновление системы."
    fi
    
    print_success "Система обновлена"
}

# Установка зависимостей
install_dependencies() {
    print_step "Установка системных зависимостей..."
    
    # Определяем пакетный менеджер и устанавливаем зависимости
    if command -v apt &> /dev/null; then
        apt install -y \
            python3-full \
            python3-venv \
            build-essential \
            nginx \
            sqlite3 \
            git \
            curl \
            wget \
            htop \
            logrotate \
            cron
    elif command -v yum &> /dev/null; then
        yum install -y \
            gcc \
            gcc-c++ \
            make \
            nginx \
            sqlite \
            git \
            curl \
            wget \
            htop \
            logrotate \
            cronie
    elif command -v dnf &> /dev/null; then
        dnf install -y \
            gcc \
            gcc-c++ \
            make \
            nginx \
            sqlite \
            git \
            curl \
            wget \
            htop \
            logrotate \
            cronie
    else
        print_warning "Неизвестный пакетный менеджер. Некоторые зависимости могут быть не установлены."
    fi
    
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
    sudo mkdir -p /opt/toyota-dashboard/logs
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
    
    # Создание директории logs если отсутствует
    if [[ ! -d "logs" ]]; then
        print_step "Создание директории logs..."
        sudo -u toyota mkdir -p logs
        print_success "Директория logs создана"
    fi
    
    # Исправление проблемы с версией pytoyoda
    if [[ -f "pytoyoda/__init__.py" ]]; then
        print_step "Исправление проблемы с версией pytoyoda..."
        sudo -u toyota sed -i 's/from importlib_metadata import version/# from importlib_metadata import version/' pytoyoda/__init__.py
        sudo -u toyota sed -i 's/__version__ = version(__name__)/__version__ = "0.0.0"/' pytoyoda/__init__.py
        print_success "Проблема с версией исправлена"
    fi
    
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
        
        # Проверка критически важных зависимостей
        echo 'Проверка критически важных зависимостей...'
        python3 -c 'import jwt; print(\"✓ PyJWT установлен:\", jwt.__version__)' || {
            echo 'Установка PyJWT...'
            pip install pyjwt==2.8.0
        }
        
        python3 -c 'import arrow; print(\"✓ Arrow установлен:\", arrow.__version__)' || {
            echo 'Установка Arrow...'
            pip install arrow==1.3.0
        }
        
        python3 -c 'import langcodes; print(\"✓ Langcodes установлен\")' || {
            echo 'Установка Langcodes...'
            pip install langcodes==3.4.0
        }
        
        echo 'Все критически важные зависимости проверены'
    " || {
        print_error "Ошибка установки Python зависимостей"
        exit 1
    }
    
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
    echo "   curl -sSL \"https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh?\$(date +%s)\" | sudo bash"
    echo
    echo -e "${GREEN}Установка завершена успешно! 🚗✨${NC}"
}

# Функция для исправления зависимостей в уже установленной системе
fix_dependencies() {
    print_step "Исправление зависимостей в установленной системе..."
    
    # Проверка существования установки
    if [[ ! -d "/opt/toyota-dashboard" ]]; then
        print_error "Toyota Dashboard не найден в /opt/toyota-dashboard"
        print_info "Запустите полную установку вместо исправления зависимостей"
        exit 1
    fi
    
    cd /opt/toyota-dashboard
    
    # Остановка сервиса
    print_step "Остановка сервиса toyota-dashboard..."
    systemctl stop toyota-dashboard || true
    
    # Проверка виртуального окружения
    if [[ ! -d "venv" ]]; then
        print_warning "Виртуальное окружение не найдено, создаем новое..."
        sudo -u toyota python3 -m venv venv
    fi
    
    # Установка недостающих зависимостей
    print_step "Установка недостающих зависимостей..."
    sudo -u toyota bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        
        # Установка критически важных зависимостей
        echo 'Установка PyJWT...'
        pip install pyjwt==2.8.0
        
        echo 'Установка Arrow...'
        pip install arrow==1.3.0
        
        echo 'Установка Langcodes...'
        pip install langcodes==3.4.0
        
        # Проверка установки
        echo 'Проверка установленных зависимостей:'
        python3 -c 'import jwt; print(\"✓ PyJWT:\", jwt.__version__)'
        python3 -c 'import arrow; print(\"✓ Arrow:\", arrow.__version__)'
        python3 -c 'import langcodes; print(\"✓ Langcodes установлен\")'
        
        echo 'Все зависимости установлены успешно'
    " || {
        print_error "Ошибка установки зависимостей"
        exit 1
    }
    
    # Создание директории logs если отсутствует
    if [[ ! -d "logs" ]]; then
        print_step "Создание директории logs..."
        sudo -u toyota mkdir -p logs
        print_success "Директория logs создана"
    fi
    
    # Исправление проблемы с версией pytoyoda
    if [[ -f "pytoyoda/__init__.py" ]]; then
        print_step "Исправление проблемы с версией pytoyoda..."
        sudo -u toyota sed -i 's/from importlib_metadata import version/# from importlib_metadata import version/' pytoyoda/__init__.py
        sudo -u toyota sed -i 's/__version__ = version(__name__)/__version__ = "0.0.0"/' pytoyoda/__init__.py
        print_success "Проблема с версией исправлена"
    fi
    
    # Запуск сервиса
    print_step "Запуск сервиса toyota-dashboard..."
    systemctl start toyota-dashboard
    
    # Проверка статуса
    sleep 3
    if systemctl is-active --quiet toyota-dashboard; then
        print_success "Toyota Dashboard сервис запущен!"
    else
        print_error "Сервис не удалось запустить. Проверьте логи: sudo journalctl -u toyota-dashboard -f"
        exit 1
    fi
    
    print_success "Зависимости исправлены успешно!"
    print_info "Проверьте статус: sudo systemctl status toyota-dashboard"
    print_info "Просмотр логов: sudo journalctl -u toyota-dashboard -f"
}

# Основная функция
main() {
    print_header
    
    # Проверка прав root
    if [[ $EUID -ne 0 ]]; then
        print_error "Этот скрипт должен быть запущен с правами root (sudo)"
        exit 1
    fi
    
    # Подтверждение установки (если не указан флаг -y)
    if [[ "$1" != "-y" && "$1" != "--yes" ]]; then
        echo -e "${YELLOW}Этот скрипт установит Toyota Dashboard на ваш Raspberry Pi.${NC}"
        echo -e "${YELLOW}Продолжить? (y/N)${NC}"
        
        # Проверяем доступность терминала
        if [[ -t 0 ]] || [[ -c /dev/tty ]]; then
            # Читаем напрямую из терминала
            read -r response < /dev/tty
        else
            # Если терминал недоступен, используем автоматическое подтверждение
            echo -e "${YELLOW}Терминал недоступен для интерактивного ввода.${NC}"
            echo -e "${YELLOW}Используйте флаг -y для автоматической установки:${NC}"
            echo "curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | sudo bash -s -- -y"
            exit 1
        fi
        
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Установка отменена"
            exit 0
        fi
    else
        echo -e "${GREEN}Автоматическая установка Toyota Dashboard...${NC}"
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

# Обработка аргументов и запуск
case "${1:-}" in
    --fix-deps|--fix-dependencies)
        print_header
        if [[ $EUID -ne 0 ]]; then
            print_error "Этот скрипт должен быть запущен с правами root (sudo)"
            exit 1
        fi
        fix_dependencies
        ;;
    *)
        main "$@"
        ;;
esac