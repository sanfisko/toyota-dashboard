#!/bin/bash

# Скрипт для обновления порта в nginx конфигурации
# Используется при изменении порта через веб-интерфейс

NEW_PORT=$1

if [[ -z "$NEW_PORT" ]]; then
    echo "Использование: $0 <новый_порт>"
    exit 1
fi

# Проверка валидности порта
if [[ ! "$NEW_PORT" =~ ^[0-9]+$ ]] || [[ "$NEW_PORT" -lt 1024 ]] || [[ "$NEW_PORT" -gt 65535 ]]; then
    echo "Ошибка: Порт должен быть числом от 1024 до 65535"
    exit 1
fi

# Обновление nginx конфигурации
NGINX_CONFIG="/etc/nginx/sites-available/toyota-dashboard"

if [[ -f "$NGINX_CONFIG" ]]; then
    # Создать резервную копию
    sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Обновить порт в конфигурации
    sudo sed -i "s/proxy_pass http:\/\/127\.0\.0\.1:[0-9]\+;/proxy_pass http:\/\/127.0.0.1:$NEW_PORT;/" "$NGINX_CONFIG"
    
    # Проверить конфигурацию nginx
    if sudo nginx -t; then
        # Перезагрузить nginx
        sudo systemctl reload nginx
        echo "Nginx конфигурация обновлена для порта $NEW_PORT"
    else
        echo "Ошибка в nginx конфигурации, восстанавливаем резервную копию"
        sudo cp "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONFIG"
        exit 1
    fi
else
    echo "Файл конфигурации nginx не найден: $NGINX_CONFIG"
    exit 1
fi