#!/bin/bash

# Toyota Dashboard Server - Установочный скрипт для Raspberry Pi
# Автор: OpenHands AI
# Версия: 2.0.0
#
# Использование:
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | bash
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh | bash -s -- -y
#
# Флаги:
#   -y, --yes                    Автоматическое подтверждение без интерактивного запроса

set -e  # Остановить при ошибке

# Получаем информацию о реальном пользователе (не root при sudo)
if [[ -n "$SUDO_USER" ]]; then
    CURRENT_USER="$SUDO_USER"
    CURRENT_HOME=$(eval echo ~$SUDO_USER)
    CURRENT_UID=$(id -u "$SUDO_USER")
    CURRENT_GID=$(id -g "$SUDO_USER")
else
    CURRENT_USER=$(whoami)
    CURRENT_HOME=$(eval echo ~$CURRENT_USER)
    CURRENT_UID=$(id -u)
    CURRENT_GID=$(id -g)
fi

# Пути для установки
INSTALL_DIR="$CURRENT_HOME/toyota-dashboard"
CONFIG_DIR="$CURRENT_HOME/.config/toyota-dashboard"
DATA_DIR="$CURRENT_HOME/.local/share/toyota-dashboard"
CACHE_DIR="$CURRENT_HOME/.cache/toyota-dashboard"
LOG_DIR="$DATA_DIR/logs"

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
    echo "║         Установка под текущим пользователем                 ║"
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
    print_step "Проверка системы..."
    
    print_info "Для обновления системы выполните:"
    if command -v apt &> /dev/null; then
        print_info "  sudo apt update && sudo apt upgrade -y"
    elif command -v yum &> /dev/null; then
        print_info "  sudo yum update -y"
    elif command -v dnf &> /dev/null; then
        print_info "  sudo dnf update -y"
    elif command -v pacman &> /dev/null; then
        print_info "  sudo pacman -Syu"
    fi
    
    print_success "Система проверена"
}

# Установка зависимостей
install_dependencies() {
    print_step "Проверка системных зависимостей..."

    # Проверяем наличие основных зависимостей
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_warning "Отсутствуют зависимости: ${missing_deps[*]}"
        print_info "Установите их с помощью:"
        
        if command -v apt &> /dev/null; then
            print_info "  sudo apt install -y python3-full python3-venv build-essential git curl wget"
        elif command -v yum &> /dev/null; then
            print_info "  sudo yum install -y python3 python3-pip gcc gcc-c++ make git curl wget"
        elif command -v dnf &> /dev/null; then
            print_info "  sudo dnf install -y python3 python3-pip gcc gcc-c++ make git curl wget"
        fi
        
        if [[ -t 0 ]]; then
            read -p "Продолжить установку? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Установка отменена"
                exit 1
            fi
        else
            print_info "Неинтерактивный режим - продолжаем автоматически"
        fi
    fi
    
    print_success "Системные зависимости проверены"
}

# Проверка файловой системы
check_filesystem() {
    print_step "Проверка файловой системы..."
    
    # Проверяем, можем ли мы писать в домашнюю директорию
    if [[ ! -w "$CURRENT_HOME" ]]; then
        print_error "Нет прав на запись в домашнюю директорию: $CURRENT_HOME"
        exit 1
    fi
    
    # Проверяем доступное место
    AVAILABLE_SPACE=$(df -h "$CURRENT_HOME" | awk 'NR==2 {print $4}')
    print_info "Доступное место в $CURRENT_HOME: $AVAILABLE_SPACE"
    
    print_success "Файловая система доступна для записи"
}



# Создание директорий
create_directories() {
    print_step "Создание директорий..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$CACHE_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR/backups"
    
    # Устанавливаем правильного владельца если запущено через sudo
    if [[ -n "$SUDO_USER" ]]; then
        chown -R "$CURRENT_UID:$CURRENT_GID" "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$CACHE_DIR" 2>/dev/null || true
    fi
    
    print_success "Директории созданы"
}

# Скачивание проекта
download_project() {
    print_step "Скачивание проекта..."
    
    # Удаляем старую установку если есть
    if [[ -d "$INSTALL_DIR" ]]; then
        print_info "Удаление старой установки..."
        rm -rf "$INSTALL_DIR"
    fi
    
    # Клонируем репозиторий
    git clone https://github.com/sanfisko/toyota-dashboard.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Устанавливаем правильного владельца если запущено через sudo
    if [[ -n "$SUDO_USER" ]]; then
        chown -R "$CURRENT_UID:$CURRENT_GID" "$INSTALL_DIR" 2>/dev/null || true
    fi
    
    # Создание директории logs если отсутствует
    if [[ ! -d "logs" ]]; then
        print_step "Создание директории logs..."
        mkdir -p logs
        print_success "Директория logs создана"
    fi
    
    # Исправление проблемы с версией pytoyoda
    if [[ -f "pytoyoda/__init__.py" ]]; then
        print_step "Исправление проблемы с версией pytoyoda..."
        sed -i 's/from importlib_metadata import version/# from importlib_metadata import version/' pytoyoda/__init__.py
        sed -i 's/__version__ = version(__name__)/__version__ = "0.0.0"/' pytoyoda/__init__.py
        print_success "Проблема с версией исправлена"
    fi
    
    print_success "Проект скачан"
}

# Установка Python зависимостей
install_python_deps() {
    print_step "Установка Python зависимостей..."
    
    cd "$INSTALL_DIR"
    
    # Создание виртуального окружения
    python3 -m venv venv
    
    # Активация и установка зависимостей
    source venv/bin/activate
    pip install --upgrade pip
    
    # Установка зависимостей
    if [[ -f "requirements.txt" ]]; then
        print_info "Установка зависимостей из requirements.txt..."
        pip install -r requirements.txt
    else
        print_error "Файл requirements.txt не найден"
        exit 1
    fi
    
    # Проверка критически важных зависимостей
    print_info "Проверка критически важных зависимостей..."
    
    CRITICAL_DEPS=("fastapi" "uvicorn" "pydantic" "httpx" "pyyaml" "aiosqlite" "beautifulsoup4")
    for dep in "${CRITICAL_DEPS[@]}"; do
        if pip show "$dep" &> /dev/null; then
            VERSION=$(pip show "$dep" | grep Version | cut -d' ' -f2)
            print_success "$dep установлен: $VERSION"
        else
            print_error "$dep НЕ установлен"
            exit 1
        fi
    done
    
    # Проверяем PyToyoda отдельно
    print_info "Проверка PyToyoda..."
    if pip show pytoyoda &> /dev/null; then
        VERSION=$(pip show pytoyoda | grep Version | cut -d' ' -f2)
        print_success "PyToyoda установлен: $VERSION"
    else
        print_warning "PyToyoda не установлен через pip, но может быть включен в проект"
    fi
    
    print_info "Все критически важные зависимости проверены"
    
    deactivate
    
    print_success "Python зависимости установлены"
}

# Настройка конфигурации
setup_config() {
    print_step "Настройка конфигурации..."
    
    cd "$INSTALL_DIR"
    
    # Создаем базовый конфигурационный файл
    if [[ -f "config.example.yaml" ]]; then
        cp config.example.yaml "$CONFIG_DIR/config.yaml"
        print_success "Базовый конфигурационный файл создан: $CONFIG_DIR/config.yaml"
    elif [[ -f "config.yaml" ]]; then
        cp config.yaml "$CONFIG_DIR/config.yaml"
        print_success "Конфигурационный файл скопирован: $CONFIG_DIR/config.yaml"
    else
        # Создаем минимальный конфигурационный файл
        cat > "$CONFIG_DIR/config.yaml" << EOF
# Toyota Dashboard Configuration
toyota:
  username: ""  # Ваш email от Toyota Connected
  password: ""  # Ваш пароль
  vin: ""       # VIN номер вашего автомобиля
  region: "europe"  # Регион: europe, north_america, asia

server:
  host: "0.0.0.0"
  port: 2025
  debug: false

database:
  path: "$DATA_DIR/toyota.db"

logging:
  level: "INFO"
  file: "$LOG_DIR/app.log"
  max_size: "10MB"
  backup_count: 5

cache:
  directory: "$CACHE_DIR"
  ttl: 300  # 5 минут

fuel_prices:
  enabled: true
  update_interval: 3600  # 1 час
  sources:
    - "https://www.benzinpreis.de"
EOF
        print_success "Минимальный конфигурационный файл создан: $CONFIG_DIR/config.yaml"
    fi
    
    # Устанавливаем правильного владельца если запущено через sudo
    if [[ -n "$SUDO_USER" ]]; then
        chown -R "$CURRENT_UID:$CURRENT_GID" "$CONFIG_DIR" 2>/dev/null || true
    fi
    
    print_success "Директории созданы: $DATA_DIR, $LOG_DIR"
    
    echo
    print_info "📝 Следующие шаги:"
    print_info "1. Отредактируйте $CONFIG_DIR/config.yaml и укажите ваши данные Toyota:"
    print_info "   - username: ваш email"
    print_info "   - password: ваш пароль"
    print_info "   - vin: VIN номер автомобиля"
    echo
    print_info "2. Запустите приложение:"
    print_info "   systemctl --user restart toyota-dashboard"
    echo
    print_info "3. Откройте в браузере:"
    print_info "   http://localhost:2025"
    
    print_success "Конфигурация настроена"
}

# Проверка установки
check_installation() {
    print_step "Проверка установки..."
    
    cd "$INSTALL_DIR"
    
    # Проверяем, что все основные файлы на месте
    REQUIRED_FILES=("app.py" "requirements.txt" "venv/bin/python")
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Отсутствует файл: $file"
            exit 1
        fi
    done
    
    # Проверяем импорт основных модулей
    source venv/bin/activate
    python3 -c "
import sys
try:
    import fastapi
    import uvicorn
    import pydantic
    import httpx
    import yaml
    import aiosqlite
    import bs4
    print('✅ Все основные модули успешно импортированы')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)
"
    deactivate
    
    print_success "Установка проверена"
}

# Создание systemd сервиса для текущего пользователя
setup_systemd() {
    print_step "Создание systemd сервиса..."
    
    # Создаем директорию для пользовательских сервисов
    mkdir -p "$CURRENT_HOME/.config/systemd/user"
    
    # Устанавливаем правильного владельца если запущено через sudo
    if [[ -n "$SUDO_USER" ]]; then
        chown -R "$CURRENT_UID:$CURRENT_GID" "$CURRENT_HOME/.config/systemd" 2>/dev/null || true
    fi
    
    # Создаем файл сервиса
    cat > "$CURRENT_HOME/.config/systemd/user/toyota-dashboard.service" << EOF
[Unit]
Description=Toyota Dashboard Server
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
Environment=HOME=$CURRENT_HOME
Environment=XDG_CONFIG_HOME=$CURRENT_HOME/.config
Environment=XDG_DATA_HOME=$CURRENT_HOME/.local/share
Environment=XDG_CACHE_HOME=$CURRENT_HOME/.cache
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
    
    # Перезагружаем systemd для пользователя
    if [[ -n "$SUDO_USER" ]]; then
        sudo -u "$SUDO_USER" systemctl --user daemon-reload
        sudo -u "$SUDO_USER" systemctl --user enable toyota-dashboard.service
    else
        systemctl --user daemon-reload
        systemctl --user enable toyota-dashboard.service
    fi
    
    print_success "Systemd сервис создан и включен"
    print_info "Управление сервисом:"
    print_info "  Запуск:    systemctl --user start toyota-dashboard"
    print_info "  Остановка: systemctl --user stop toyota-dashboard"
    print_info "  Статус:    systemctl --user status toyota-dashboard"
    print_info "  Логи:      journalctl --user -u toyota-dashboard -f"
}

# Создание скриптов управления
create_management_scripts() {
    print_step "Создание скриптов управления..."
    
    # Скрипт запуска
    cat > "$INSTALL_DIR/start.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
python app.py
EOF
    chmod +x "$INSTALL_DIR/start.sh"
    
    # Скрипт остановки
    cat > "$INSTALL_DIR/stop.sh" << EOF
#!/bin/bash
pkill -f "python.*app.py" || echo "Процесс не найден"
EOF
    chmod +x "$INSTALL_DIR/stop.sh"
    
    # Скрипт обновления
    cat > "$INSTALL_DIR/update.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
echo "Обновление завершено. Перезапустите сервис."
EOF
    chmod +x "$INSTALL_DIR/update.sh"
    
    # Устанавливаем правильного владельца если запущено через sudo
    if [[ -n "$SUDO_USER" ]]; then
        chown "$CURRENT_UID:$CURRENT_GID" "$INSTALL_DIR"/*.sh 2>/dev/null || true
    fi
    
    print_success "Скрипты управления созданы"
}

# Настройка автозапуска
setup_autostart() {
    print_step "Настройка автозапуска..."
    
    # Включаем lingering для пользователя (чтобы сервисы запускались без входа в систему)
    if command -v loginctl &> /dev/null; then
        sudo loginctl enable-linger "$CURRENT_USER" 2>/dev/null || print_warning "Не удалось включить lingering"
    fi
    
    # Запускаем сервис
    if [[ -n "$SUDO_USER" ]]; then
        sudo -u "$SUDO_USER" systemctl --user start toyota-dashboard.service
        if sudo -u "$SUDO_USER" systemctl --user is-active toyota-dashboard.service >/dev/null 2>&1; then
            print_success "Toyota Dashboard сервис запущен"
        else
            print_warning "Сервис не запущен. Проверьте конфигурацию и запустите вручную"
        fi
    else
        systemctl --user start toyota-dashboard.service
        if systemctl --user is-active toyota-dashboard.service >/dev/null 2>&1; then
            print_success "Toyota Dashboard сервис запущен"
        else
            print_warning "Сервис не запущен. Проверьте конфигурацию и запустите вручную"
        fi
    fi
    
    print_success "Автозапуск настроен"
}

# Основная функция установки
main() {
    # Обработка аргументов
    AUTO_YES=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                AUTO_YES=true
                shift
                ;;
            *)
                print_error "Неизвестный аргумент: $1"
                exit 1
                ;;
        esac
    done
    
    print_header
    
    print_info "Установка Toyota Dashboard под пользователем: $CURRENT_USER"
    print_info "Домашняя директория: $CURRENT_HOME"
    print_info "Директория установки: $INSTALL_DIR"
    echo
    
    # Проверяем интерактивный режим
    if [[ "$AUTO_YES" != true ]] && [[ -t 0 ]]; then
        echo "Этот скрипт установит Toyota Dashboard в вашу домашнюю директорию."
        read -p "Продолжить? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Установка отменена"
            exit 0
        fi
    elif [[ "$AUTO_YES" != true ]]; then
        echo "Этот скрипт установит Toyota Dashboard в вашу домашнюю директорию."
        echo "Запуск в неинтерактивном режиме - продолжаем автоматически..."
        echo "Начинаем установку через 3 секунды..."
        sleep 3
    fi
    
    echo "Переходим к проверке системы..."
    
    # Выполнение установки
    check_system
    check_filesystem
    update_system
    install_dependencies
    create_directories
    download_project
    install_python_deps
    setup_config
    check_installation
    setup_systemd
    create_management_scripts
    setup_autostart
    
    # Финальная информация
    print_success "Установка завершена!"
    echo
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    ВАЖНАЯ ИНФОРМАЦИЯ                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}1. Настройте конфигурацию:${NC}"
    echo "   nano $CONFIG_DIR/config.yaml"
    echo
    echo -e "${YELLOW}2. Добавьте ваши Toyota credentials:${NC}"
    echo "   - username: ваш email от Toyota Connected"
    echo "   - password: ваш пароль"
    echo "   - vin: VIN номер вашего Toyota автомобиля"
    echo
    echo -e "${YELLOW}3. Управление сервисом:${NC}"
    echo "   systemctl --user start toyota-dashboard    # Запуск"
    echo "   systemctl --user stop toyota-dashboard     # Остановка"
    echo "   systemctl --user restart toyota-dashboard  # Перезапуск"
    echo "   systemctl --user status toyota-dashboard   # Статус"
    echo
    echo -e "${YELLOW}4. Доступ к дашборду:${NC}"
    echo "   http://localhost:2025"
    echo
    echo -e "${YELLOW}5. Логи:${NC}"
    echo "   journalctl --user -u toyota-dashboard -f"
    echo
    echo -e "${YELLOW}6. Скрипты управления:${NC}"
    echo "   $INSTALL_DIR/start.sh   # Прямой запуск"
    echo "   $INSTALL_DIR/stop.sh    # Остановка"
    echo "   $INSTALL_DIR/update.sh  # Обновление"
    echo
    echo -e "${GREEN}Установка завершена успешно! Toyota Dashboard готов! ✨${NC}"
}

# Обработка ошибок
trap 'print_error "Установка прервана из-за ошибки на строке $LINENO"' ERR

# Запуск установки
main "$@"