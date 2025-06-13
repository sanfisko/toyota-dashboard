#!/bin/bash

# Тестовая версия install.sh для проверки логики
# Не выполняет реальную установку

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции для вывода
print_step() {
    echo -e "${GREEN}[TEST-STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[TEST-INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[TEST-SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[TEST-ERROR]${NC} $1"
}

# Тестирование функции установки Python зависимостей
test_install_python_deps() {
    print_step "Тестирование установки Python зависимостей..."
    
    # Симуляция создания директории
    TEST_DIR="/tmp/test-toyota-dashboard"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    
    # Копируем файлы зависимостей для тестирования
    cp /workspace/toyota-dashboard/requirements*.txt . 2>/dev/null || true
    
    # Тестирование логики выбора файла зависимостей
    if [[ -f requirements-simple.txt ]]; then
        print_info "✓ Найден requirements-simple.txt - будет использован"
        echo "Содержимое requirements-simple.txt:"
        head -10 requirements-simple.txt
    elif [[ -f requirements-optimized.txt ]]; then
        print_info "✓ Найден requirements-optimized.txt - будет использован"
    else
        print_info "✓ Будет использован requirements.txt"
    fi
    
    # Тестирование bash синтаксиса для проверки зависимостей
    print_step "Тестирование bash команд..."
    
    # Симуляция команд проверки (без реального выполнения Python)
    echo "Тестирование команды FastAPI..."
    TEST_CMD='import sys; print("✓ FastAPI тест:", "0.104.1")'
    echo "python3 -c '$TEST_CMD'" 
    
    echo "Тестирование команды PyToyoda..."
    TEST_CMD='import sys; print("✓ PyToyoda тест:", getattr(sys, "version", "тестовая версия"))'
    echo "python3 -c '$TEST_CMD'"
    
    # Очистка
    rm -rf "$TEST_DIR"
    
    print_success "Тестирование завершено успешно"
}

# Тестирование bash синтаксиса
test_bash_syntax() {
    print_step "Проверка синтаксиса bash..."
    
    # Проверяем основной скрипт
    if bash -n /workspace/toyota-dashboard/install.sh; then
        print_success "✓ Синтаксис install.sh корректен"
    else
        print_error "✗ Ошибка синтаксиса в install.sh"
        return 1
    fi
}

# Тестирование файлов зависимостей
test_requirements_files() {
    print_step "Проверка файлов зависимостей..."
    
    cd /workspace/toyota-dashboard
    
    for req_file in requirements.txt requirements-simple.txt requirements-optimized.txt; do
        if [[ -f "$req_file" ]]; then
            print_info "✓ Найден $req_file"
            echo "  Количество строк: $(wc -l < "$req_file")"
            echo "  Основные пакеты:"
            grep -E "^(fastapi|uvicorn|pytoyoda|loguru)" "$req_file" || echo "    (основные пакеты не найдены)"
        else
            print_info "✗ Не найден $req_file"
        fi
    done
}

# Основная функция тестирования
main() {
    echo "🧪 Тестирование Toyota Dashboard Install Script"
    echo "================================================"
    
    test_bash_syntax
    test_requirements_files
    test_install_python_deps
    
    echo ""
    echo "🎉 Все тесты завершены!"
}

main "$@"