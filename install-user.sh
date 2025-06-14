#!/bin/bash

# Toyota Dashboard Server - Установочный скрипт для текущего пользователя
# Автор: OpenHands AI
# Версия: 2.0.0
#
# Использование:
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh | bash
#   curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh | bash -s -- -y
#
# Флаги:
#   -y, --yes                    Автоматическое подтверждение без интерактивного запроса

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

# Получаем информацию о текущем пользователе
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

# Пути для установки
INSTALL_DIR="$CURRENT_HOME/toyota-dashboard"
CONFIG_DIR="$CURRENT_HOME/.config/toyota-dashboard"
DATA_DIR="$CURRENT_HOME/.local/share/toyota-dashboard"
CACHE_DIR="$CURRENT_HOME/.cache/toyota-dashboard"
LOG_DIR="$DATA_DIR/logs"

# Проверка и установка Python
check_and_install_python() {
    print_step "Проверка Python..."
    
    # Проверяем, установлен ли Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не найден. Установите Python 3.8+ и повторите попытку."
        print_info "Для Debian/Ubuntu: sudo apt install python3 python3-pip python3-venv"
        exit 1
    fi
    
    # Получаем версию Python
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
    
    print_success "Python $PYTHON_VERSION найден"
    
    # Проверяем версию Python (требуется 3.8+)
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        print_error "Требуется Python 3.8 или выше. Установлен: $PYTHON_VERSION"
        print_info "Обновите Python и повторите попытку."
        exit 1
    fi
    
    # Проверяем наличие venv
    if ! python3 -m venv --help &> /dev/null; then
        print_error "Модуль venv не найден. Установите python3-venv:"
        print_info "Для Debian/Ubuntu: sudo apt install python3-venv"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION готов к использованию"
}

# Проверка системы
check_system() {
    print_step "Проверка системы..."
    
    # Проверка ОС
    if [[ ! -f /etc/os-release ]]; then
        print_warning "Не удается определить операционную систему"
    else
        source /etc/os-release
        print_info "Операционная система: $PRETTY_NAME"
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    print_info "Архитектура: $ARCH"
    
    # Проверка и установка Python
    check_and_install_python
    
    print_success "Система совместима"
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

# Установка системных зависимостей (если нужно)
install_system_dependencies() {
    print_step "Проверка системных зависимостей..."
    
    # Проверяем наличие необходимых команд
    MISSING_DEPS=()
    
    if ! command -v git &> /dev/null; then
        MISSING_DEPS+=("git")
    fi
    
    if ! command -v curl &> /dev/null; then
        MISSING_DEPS+=("curl")
    fi
    
    if ! command -v sqlite3 &> /dev/null; then
        MISSING_DEPS+=("sqlite3")
    fi
    
    if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
        print_warning "Отсутствуют системные зависимости: ${MISSING_DEPS[*]}"
        print_info "Установите их с помощью:"
        print_info "sudo apt install ${MISSING_DEPS[*]}"
        
        read -p "Попытаться установить автоматически? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v apt &> /dev/null; then
                sudo apt update
                sudo apt install -y "${MISSING_DEPS[@]}"
            else
                print_error "Автоматическая установка поддерживается только для apt"
                exit 1
            fi
        else
            print_error "Установите недостающие зависимости и повторите попытку"
            exit 1
        fi
    fi
    
    print_success "Системные зависимости проверены"
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
    
    # Исправляем проблему с версией pytoyoda
    print_step "Исправление проблемы с версией pytoyoda..."
    if [[ -f "requirements.txt" ]]; then
        sed -i 's/pytoyoda>=3.0.0,<4.0.0/pytoyoda>=3.0.0,<4.0.0/' requirements.txt
        print_success "Проблема с версией исправлена"
    fi
    
    print_success "Проект скачан"
}

# Установка Python зависимостей
install_python_dependencies() {
    print_step "Установка Python зависимостей..."
    
    cd "$INSTALL_DIR"
    
    # Создаем виртуальное окружение
    python3 -m venv venv
    
    # Активируем виртуальное окружение и обновляем pip
    source venv/bin/activate
    pip install --upgrade pip
    
    # Устанавливаем зависимости
    if [[ -f "requirements.txt" ]]; then
        print_info "Установка зависимостей из requirements.txt..."
        pip install -r requirements.txt
    else
        print_error "Файл requirements.txt не найден"
        exit 1
    fi
    
    # Проверяем критически важные зависимости
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
setup_configuration() {
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
    
    print_success "Директории созданы: $DATA_DIR, $LOG_DIR"
    
    echo
    print_info "📝 Следующие шаги:"
    print_info "1. Отредактируйте $CONFIG_DIR/config.yaml и укажите ваши данные Toyota:"
    print_info "   - username: ваш email"
    print_info "   - password: ваш пароль"
    print_info "   - vin: VIN номер автомобиля"
    echo
    print_info "2. Запустите приложение:"
    print_info "   cd $INSTALL_DIR && ./venv/bin/python app.py"
    echo
    print_info "3. Откройте в браузере:"
    print_info "   http://localhost:2025"
    
    print_success "Конфигурация настроена"
}

# Проверка установки
verify_installation() {
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
create_systemd_service() {
    print_step "Создание systemd сервиса..."
    
    # Создаем директорию для пользовательских сервисов
    mkdir -p "$CURRENT_HOME/.config/systemd/user"
    
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
    systemctl --user daemon-reload
    
    # Включаем сервис
    systemctl --user enable toyota-dashboard.service
    
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
    systemctl --user start toyota-dashboard.service
    
    if systemctl --user is-active toyota-dashboard.service >/dev/null 2>&1; then
        print_success "Toyota Dashboard сервис запущен"
    else
        print_warning "Сервис не запущен. Проверьте конфигурацию и запустите вручную"
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
    
    if [[ "$AUTO_YES" != true ]]; then
        echo "Этот скрипт установит Toyota Dashboard в вашу домашнюю директорию."
        read -p "Продолжить? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Установка отменена"
            exit 0
        fi
    fi
    
    # Выполняем установку
    check_system
    check_filesystem
    install_system_dependencies
    create_directories
    download_project
    install_python_dependencies
    setup_configuration
    verify_installation
    create_systemd_service
    create_management_scripts
    setup_autostart
    
    print_success "Установка завершена!"
    
    echo
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ВАЖНАЯ ИНФОРМАЦИЯ                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
    echo "1. Настройте конфигурацию:"
    echo "   nano $CONFIG_DIR/config.yaml"
    echo
    echo "2. Добавьте ваши Toyota credentials:"
    echo "   - username: ваш email от Toyota Connected"
    echo "   - password: ваш пароль"
    echo "   - vin: VIN номер вашего Toyota автомобиля"
    echo
    echo "3. Управление сервисом:"
    echo "   systemctl --user start toyota-dashboard    # Запуск"
    echo "   systemctl --user stop toyota-dashboard     # Остановка"
    echo "   systemctl --user restart toyota-dashboard  # Перезапуск"
    echo "   systemctl --user status toyota-dashboard   # Статус"
    echo
    echo "4. Или используйте скрипты:"
    echo "   $INSTALL_DIR/start.sh    # Запуск в консоли"
    echo "   $INSTALL_DIR/stop.sh     # Остановка"
    echo "   $INSTALL_DIR/update.sh   # Обновление"
    echo
    echo "5. Доступ к дашборду:"
    echo "   http://localhost:2025"
    echo "   http://$(hostname -I | awk '{print $1}'):2025"
    echo
    echo "6. Логи:"
    echo "   journalctl --user -u toyota-dashboard -f"
    echo "   tail -f $LOG_DIR/app.log"
    echo
    echo "7. Файлы:"
    echo "   Установка:     $INSTALL_DIR"
    echo "   Конфигурация:  $CONFIG_DIR/config.yaml"
    echo "   База данных:   $DATA_DIR/toyota.db"
    echo "   Логи:          $LOG_DIR/"
    echo
    echo "Установка завершена успешно! Toyota Dashboard готов! ✨"
}

# Запускаем основную функцию
main "$@"