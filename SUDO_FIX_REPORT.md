# Отчет об исправлении проблемы с sudo в install.sh

## Проблема
Скрипт `install.sh` некорректно работал при запуске через `sudo`, так как:
1. Неправильно определял пользователя (использовал `root` вместо реального пользователя)
2. Останавливался при запуске через `curl | bash` из-за ожидания интерактивного ввода
3. Создавал файлы с неправильным владельцем
4. Команды `systemctl --user` выполнялись от имени root, что приводило к ошибкам

## Исправления в install.sh

### 1. Определение реального пользователя
```bash
# Определяем реального пользователя (даже при запуске через sudo)
if [[ -n "$SUDO_USER" ]]; then
    CURRENT_USER="$SUDO_USER"
    CURRENT_UID=$(id -u "$SUDO_USER")
    CURRENT_GID=$(id -g "$SUDO_USER")
else
    CURRENT_USER="$USER"
    CURRENT_UID=$(id -u)
    CURRENT_GID=$(id -g)
fi
```

### 2. Исправление команд systemctl
Все команды `systemctl --user` теперь выполняются от имени правильного пользователя:
```bash
if [[ -n "$SUDO_USER" ]]; then
    sudo -u "$SUDO_USER" systemctl --user daemon-reload
    sudo -u "$SUDO_USER" systemctl --user enable toyota-dashboard.service
    sudo -u "$SUDO_USER" systemctl --user start toyota-dashboard.service
else
    systemctl --user daemon-reload
    systemctl --user enable toyota-dashboard.service
    systemctl --user start toyota-dashboard.service
fi
```

### 3. Установка правильного владельца файлов
Добавлена установка правильного владельца для всех создаваемых файлов и директорий:
```bash
if [[ -n "$SUDO_USER" ]]; then
    chown -R "$CURRENT_UID:$CURRENT_GID" "$INSTALL_DIR"
    chown -R "$CURRENT_UID:$CURRENT_GID" "$CONFIG_DIR"
    chown -R "$CURRENT_UID:$CURRENT_GID" "$CURRENT_HOME/.config/systemd"
fi
```

### 4. Поддержка неинтерактивного режима
Добавлено автоматическое определение неинтерактивного режима для работы с `curl | bash`:
```bash
# Проверяем интерактивный режим
if [[ "$AUTO_YES" != true ]] && [[ -t 0 ]]; then
    # Интерактивный режим - запрашиваем подтверждение
    read -p "Продолжить? (y/N) " -n 1 -r
elif [[ "$AUTO_YES" != true ]]; then
    # Неинтерактивный режим - продолжаем автоматически
    echo "Запуск в неинтерактивном режиме - продолжаем автоматически..."
fi
```

## Исправления в uninstall.sh

### 1. Исправление команд systemctl
Аналогично install.sh, все команды `systemctl --user` теперь выполняются от имени правильного пользователя:
```bash
if [[ -n "$SUDO_USER" ]]; then
    sudo -u "$SUDO_USER" systemctl --user stop toyota-dashboard.service
    sudo -u "$SUDO_USER" systemctl --user disable toyota-dashboard.service
    sudo -u "$SUDO_USER" systemctl --user daemon-reload
else
    systemctl --user stop toyota-dashboard.service
    systemctl --user disable toyota-dashboard.service
    systemctl --user daemon-reload
fi
```

## Результат

### ✅ Что исправлено:
1. **Корректное определение пользователя** - скрипт правильно определяет реального пользователя при запуске через sudo
2. **Работа с systemctl** - все пользовательские сервисы создаются и управляются от имени правильного пользователя
3. **Правильные права доступа** - все файлы и директории создаются с правильным владельцем
4. **Неинтерактивный режим** - скрипт корректно работает при запуске через `curl | bash`
5. **Совместимость** - скрипт работает как с sudo, так и без него

### 🧪 Тестирование:
- ✅ Запуск без sudo: `bash install.sh`
- ✅ Запуск с sudo: `sudo bash install.sh`
- ✅ Запуск через curl: `curl -sSL "url" | sudo bash`
- ✅ Удаление с sudo: `sudo bash uninstall.sh`

### 📝 Использование:
```bash
# Установка (любой из способов):
bash install.sh
sudo bash install.sh
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh" | sudo bash

# Удаление:
sudo bash uninstall.sh
```

Все изменения сохранены в main ветку репозитория.