# Исправление проблемы автозапуска Toyota Dashboard

## Проблема
После установки Toyota Dashboard сервер не запускается автоматически при перезагрузке из-за проблем с systemd user session в SSH окружении.

## Решение

### 1. Обновите скрипт установки
Используйте обновленную версию скрипта установки:

```bash
curl -sSL "https://raw.githubusercontent.com/YorkMable0tqe/toyota-dashboard/improve-autostart-install/install.sh" | sudo bash
```

### 2. Или исправьте существующую установку

#### Вариант A: Активируйте systemd сервис (рекомендуется)
```bash
# Перейдите в директорию установки
cd ~/toyota-dashboard

# Запустите скрипт активации systemd
./enable_systemd.sh
```

#### Вариант B: Проверьте cron автозапуск
```bash
# Проверьте, есть ли задача в crontab
crontab -l | grep toyota-dashboard

# Если нет, добавьте вручную
(crontab -l 2>/dev/null; echo "@reboot $HOME/toyota-dashboard/autostart.sh") | crontab -
```

### 3. Проверка работы автозапуска

#### Проверка systemd сервиса:
```bash
# Проверить статус
systemctl --user status toyota-dashboard

# Посмотреть логи
journalctl --user -u toyota-dashboard -f

# Перезапустить сервис
systemctl --user restart toyota-dashboard
```

#### Проверка cron автозапуска:
```bash
# Проверить логи автозапуска
tail -f ~/toyota-dashboard/logs/autostart.log

# Проверить crontab
crontab -l
```

### 4. Ручной запуск (если автозапуск не работает)
```bash
# Прямой запуск
~/toyota-dashboard/start.sh

# Или через systemd
systemctl --user start toyota-dashboard
```

## Что исправлено в новой версии

1. **Надежный cron автозапуск**: Всегда настраивается как основной метод
2. **Улучшенный systemd**: Правильная настройка переменных окружения
3. **Lingering**: Автоматическое включение для запуска без входа в систему
4. **Скрипт активации**: `enable_systemd.sh` для ручной настройки systemd
5. **Улучшенные логи**: Подробное логирование процесса автозапуска

## Диагностика проблем

### Проверить, запущен ли сервер:
```bash
ps aux | grep "python.*app.py"
curl http://localhost:2025
```

### Проверить логи:
```bash
# Логи автозапуска
tail -f ~/toyota-dashboard/logs/autostart.log

# Логи сервера
tail -f ~/toyota-dashboard/logs/server.log

# Systemd логи
journalctl --user -u toyota-dashboard -f
```

### Проверить настройки:
```bash
# Crontab
crontab -l

# Systemd сервис
systemctl --user status toyota-dashboard

# Lingering
loginctl show-user $(whoami) | grep Linger
```

## Контакты
Если проблема не решается, создайте issue в репозитории с логами и описанием проблемы.