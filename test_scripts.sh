#!/bin/bash

# Тестовый скрипт для проверки install.sh и uninstall.sh
# Проверяет основные функции без фактической установки

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Проверка синтаксиса скриптов
test_syntax() {
    print_test "Проверка синтаксиса install.sh..."
    if bash -n install.sh; then
        print_pass "install.sh синтаксически корректен"
    else
        print_fail "install.sh содержит синтаксические ошибки"
        return 1
    fi
    
    print_test "Проверка синтаксиса uninstall.sh..."
    if bash -n uninstall.sh; then
        print_pass "uninstall.sh синтаксически корректен"
    else
        print_fail "uninstall.sh содержит синтаксические ошибки"
        return 1
    fi
}

# Проверка функций в install.sh
test_install_functions() {
    print_test "Проверка функций в install.sh..."
    
    # Извлекаем список функций
    FUNCTIONS=$(grep -E "^[a-zA-Z_][a-zA-Z0-9_]*\(\)" install.sh | cut -d'(' -f1)
    
    EXPECTED_FUNCTIONS=(
        "print_header"
        "print_step"
        "print_info"
        "print_warning"
        "print_error"
        "print_success"
        "check_and_install_python"
        "check_system"
        "update_system"
        "install_dependencies"
        "check_filesystem"
        "create_directories"
        "download_project"
        "install_python_deps"
        "setup_config"
        "check_installation"
        "check_systemd_user"
        "setup_systemd"
        "create_management_scripts"
        "setup_autostart"
        "main"
    )
    
    for func in "${EXPECTED_FUNCTIONS[@]}"; do
        if echo "$FUNCTIONS" | grep -q "^$func$"; then
            print_pass "Функция $func найдена"
        else
            print_fail "Функция $func отсутствует"
        fi
    done
}

# Проверка функций в uninstall.sh
test_uninstall_functions() {
    print_test "Проверка функций в uninstall.sh..."
    
    # Извлекаем список функций
    FUNCTIONS=$(grep -E "^[a-zA-Z_][a-zA-Z0-9_]*\(\)" uninstall.sh | cut -d'(' -f1)
    
    EXPECTED_FUNCTIONS=(
        "print_header"
        "print_success"
        "print_warning"
        "print_error"
        "print_info"
        "main"
    )
    
    for func in "${EXPECTED_FUNCTIONS[@]}"; do
        if echo "$FUNCTIONS" | grep -q "^$func$"; then
            print_pass "Функция $func найдена"
        else
            print_fail "Функция $func отсутствует"
        fi
    done
}

# Проверка ссылок на репозиторий
test_repository_links() {
    print_test "Проверка ссылок на репозиторий..."
    
    # Проверяем install.sh
    if grep -q "github.com/sanfisko/toyota-dashboard" install.sh; then
        print_pass "install.sh содержит правильные ссылки на репозиторий"
    else
        print_fail "install.sh содержит неправильные ссылки на репозиторий"
    fi
    
    # Проверяем uninstall.sh
    if grep -q "sanfisko/toyota-dashboard" uninstall.sh; then
        print_pass "uninstall.sh содержит правильные ссылки на репозиторий"
    else
        print_fail "uninstall.sh содержит неправильные ссылки на репозиторий"
    fi
}

# Проверка обработки аргументов
test_argument_handling() {
    print_test "Проверка обработки аргументов..."
    
    # Проверяем install.sh
    if grep -q "\-y\|--yes" install.sh; then
        print_pass "install.sh поддерживает флаг -y/--yes"
    else
        print_fail "install.sh не поддерживает флаг -y/--yes"
    fi
    
    # Проверяем uninstall.sh
    if grep -q "\-y\|--yes" uninstall.sh && grep -q "\-h\|--help" uninstall.sh; then
        print_pass "uninstall.sh поддерживает флаги -y/--yes и -h/--help"
    else
        print_fail "uninstall.sh не поддерживает необходимые флаги"
    fi
}

# Проверка обработки ошибок
test_error_handling() {
    print_test "Проверка обработки ошибок..."
    
    # Проверяем наличие set -e
    if grep -q "set -e" install.sh && grep -q "set -e" uninstall.sh; then
        print_pass "Оба скрипта используют set -e для обработки ошибок"
    else
        print_fail "Не все скрипты используют set -e"
    fi
    
    # Проверяем trap в install.sh
    if grep -q "trap.*ERR" install.sh; then
        print_pass "install.sh использует trap для обработки ошибок"
    else
        print_fail "install.sh не использует trap для обработки ошибок"
    fi
}

# Проверка systemd функций
test_systemd_handling() {
    print_test "Проверка обработки systemd..."
    
    # Проверяем функцию check_systemd_user
    if grep -q "check_systemd_user" install.sh; then
        print_pass "install.sh содержит проверку доступности systemd"
    else
        print_fail "install.sh не проверяет доступность systemd"
    fi
    
    # Проверяем обработку недоступности systemd
    if grep -q "недоступен" install.sh; then
        print_pass "install.sh обрабатывает недоступность systemd"
    else
        print_fail "install.sh не обрабатывает недоступность systemd"
    fi
}

# Основная функция тестирования
main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  ТЕСТИРОВАНИЕ СКРИПТОВ                      ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    local failed_tests=0
    
    test_syntax || ((failed_tests++))
    echo
    
    test_install_functions || ((failed_tests++))
    echo
    
    test_uninstall_functions || ((failed_tests++))
    echo
    
    test_repository_links || ((failed_tests++))
    echo
    
    test_argument_handling || ((failed_tests++))
    echo
    
    test_error_handling || ((failed_tests++))
    echo
    
    test_systemd_handling || ((failed_tests++))
    echo
    
    if [[ $failed_tests -eq 0 ]]; then
        print_pass "Все тесты пройдены успешно!"
        return 0
    else
        print_fail "Провалено тестов: $failed_tests"
        return 1
    fi
}

# Запуск тестов
main "$@"