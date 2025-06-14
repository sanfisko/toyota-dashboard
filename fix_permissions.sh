#!/bin/bash
# Скрипт для исправления прав доступа Toyota Dashboard

echo "🔧 Исправление прав доступа Toyota Dashboard"
echo "=============================================="

# Определяем пользователя
TOYOTA_USER="toyota"
CURRENT_USER=$(whoami)

echo "Текущий пользователь: $CURRENT_USER"
echo "Пользователь Toyota: $TOYOTA_USER"

# Проверяем, существует ли пользователь toyota
if ! id "$TOYOTA_USER" &>/dev/null; then
    echo "❌ Пользователь $TOYOTA_USER не найден"
    echo "Создаем пользователя..."
    sudo useradd -r -s /bin/false -d /home/toyota -m toyota
    echo "✅ Пользователь $TOYOTA_USER создан"
fi

# Системные директории
SYSTEM_DIRS=(
    "/etc/toyota-dashboard"
    "/var/lib/toyota-dashboard"
    "/var/log/toyota-dashboard"
    "/opt/toyota-dashboard"
)

# Пользовательские директории
USER_DIRS=(
    "/home/$TOYOTA_USER/.config/toyota-dashboard"
    "/home/$TOYOTA_USER/.local/share/toyota-dashboard"
    "/home/$TOYOTA_USER/.local/share/toyota-dashboard/logs"
    "/home/$TOYOTA_USER/.cache/toyota-dashboard"
)

echo ""
echo "📁 Создание и настройка системных директорий..."

for dir in "${SYSTEM_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Создание: $dir"
        sudo mkdir -p "$dir"
    else
        echo "Существует: $dir"
    fi
    
    # Устанавливаем права доступа
    sudo chown -R $TOYOTA_USER:$TOYOTA_USER "$dir"
    sudo chmod -R 755 "$dir"
    echo "✅ Права настроены для: $dir"
done

echo ""
echo "🏠 Создание и настройка пользовательских директорий..."

for dir in "${USER_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Создание: $dir"
        sudo -u $TOYOTA_USER mkdir -p "$dir"
    else
        echo "Существует: $dir"
    fi
    
    # Устанавливаем права доступа
    sudo chown -R $TOYOTA_USER:$TOYOTA_USER "$dir"
    sudo chmod -R 755 "$dir"
    echo "✅ Права настроены для: $dir"
done

echo ""
echo "⚙️ Копирование конфигурации..."

# Копируем конфигурацию из системной директории в пользовательскую
SYSTEM_CONFIG="/etc/toyota-dashboard/config.yaml"
USER_CONFIG="/home/$TOYOTA_USER/.config/toyota-dashboard/config.yaml"

if [ -f "$SYSTEM_CONFIG" ] && [ ! -f "$USER_CONFIG" ]; then
    echo "Копирование конфигурации: $SYSTEM_CONFIG -> $USER_CONFIG"
    sudo cp "$SYSTEM_CONFIG" "$USER_CONFIG"
    sudo chown $TOYOTA_USER:$TOYOTA_USER "$USER_CONFIG"
    sudo chmod 644 "$USER_CONFIG"
    echo "✅ Конфигурация скопирована"
elif [ -f "$USER_CONFIG" ]; then
    echo "✅ Пользовательская конфигурация уже существует: $USER_CONFIG"
else
    echo "⚠️ Системная конфигурация не найдена: $SYSTEM_CONFIG"
fi

echo ""
echo "🔍 Проверка прав доступа..."

# Функция для проверки прав доступа
check_permissions() {
    local path="$1"
    local name="$2"
    
    if [ -e "$path" ]; then
        local owner=$(stat -c '%U' "$path")
        local perms=$(stat -c '%a' "$path")
        echo "  $name: $path"
        echo "    Владелец: $owner"
        echo "    Права: $perms"
        
        if [ "$owner" = "$TOYOTA_USER" ]; then
            echo "    ✅ Владелец корректный"
        else
            echo "    ⚠️ Владелец некорректный (ожидается: $TOYOTA_USER)"
        fi
        
        if sudo -u $TOYOTA_USER test -w "$path"; then
            echo "    ✅ Доступен для записи"
        else
            echo "    ❌ Недоступен для записи"
        fi
    else
        echo "  $name: $path - НЕ СУЩЕСТВУЕТ"
    fi
    echo ""
}

echo "Системные директории:"
for dir in "${SYSTEM_DIRS[@]}"; do
    check_permissions "$dir" "$(basename "$dir")"
done

echo "Пользовательские директории:"
for dir in "${USER_DIRS[@]}"; do
    check_permissions "$dir" "$(basename "$dir")"
done

echo "Файлы конфигурации:"
check_permissions "$SYSTEM_CONFIG" "Системная конфигурация"
check_permissions "$USER_CONFIG" "Пользовательская конфигурация"

echo ""
echo "🔄 Перезапуск сервиса..."

if systemctl is-active --quiet toyota-dashboard; then
    echo "Останавливаем сервис..."
    sudo systemctl stop toyota-dashboard
fi

echo "Запускаем сервис..."
sudo systemctl start toyota-dashboard

# Ждем немного и проверяем статус
sleep 3

if systemctl is-active --quiet toyota-dashboard; then
    echo "✅ Сервис Toyota Dashboard запущен успешно"
else
    echo "❌ Ошибка запуска сервиса"
    echo "Проверьте логи: sudo journalctl -u toyota-dashboard -n 20"
fi

echo ""
echo "✅ Исправление прав доступа завершено!"
echo ""
echo "📋 Рекомендации:"
echo "1. Проверьте статус сервиса: sudo systemctl status toyota-dashboard"
echo "2. Просмотрите логи: sudo journalctl -u toyota-dashboard -f"
echo "3. Откройте веб-интерфейс: http://$(hostname -I | awk '{print $1}')"
echo "4. Используйте диагностику: http://$(hostname -I | awk '{print $1}')/diagnostics"