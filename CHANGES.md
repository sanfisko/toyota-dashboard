# Изменения в Toyota Dashboard - Пользовательская установка

## Что изменилось

Скрипты установки и удаления полностью переработаны для работы под текущим пользователем вместо создания отдельного пользователя `toyota`.

## Основные изменения

### install.sh
- ✅ Работает под текущим пользователем (без создания пользователя toyota)
- ✅ Установка в `~/toyota-dashboard` вместо `/opt/toyota-dashboard`
- ✅ Пользовательский systemd сервис в `~/.config/systemd/user/`
- ✅ Удалены все sudo команды из основных функций
- ✅ Убраны nginx, logging, backup, firewall (не нужны для пользовательской установки)
- ✅ Добавлены скрипты управления: `start.sh`, `stop.sh`, `update.sh`

### uninstall.sh
- ✅ Удаляет пользовательскую установку
- ✅ Работает с пользовательскими путями
- ✅ Останавливает пользовательский сервис

### Новая структура установки
```
~/toyota-dashboard/           # Основная директория
├── app.py                   # Главное приложение
├── venv/                    # Виртуальное окружение
├── config.yaml              # Конфигурация
├── start.sh                 # Запуск сервиса
├── stop.sh                  # Остановка сервиса
└── update.sh                # Обновление

~/.config/systemd/user/
└── toyota-dashboard.service # Пользовательский сервис

~/.config/toyota-dashboard/
└── config.yaml              # Пользовательская конфигурация

~/.local/share/toyota-dashboard/
└── toyota.db                # База данных

~/.cache/toyota-dashboard/    # Кэш
```

## Как использовать

### Установка
```bash
bash <(curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh)
```

### Управление сервисом
```bash
# Запуск
~/toyota-dashboard/start.sh

# Остановка  
~/toyota-dashboard/stop.sh

# Статус
systemctl --user status toyota-dashboard

# Логи
journalctl --user -u toyota-dashboard -f
```

### Удаление
```bash
bash <(curl -sSL https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh)
```

## Преимущества нового подхода

1. **Безопасность**: Не создается системный пользователь
2. **Простота**: Меньше системных зависимостей
3. **Изоляция**: Все файлы в домашней директории пользователя
4. **Удобство**: Легче управлять и удалять
5. **Права**: Не нужны sudo права для основных операций

## Решенные проблемы

- ❌ Проблемы с правами доступа к `/home/toyota`
- ❌ Ошибки создания директорий
- ❌ Проблемы с systemd сервисом
- ❌ Сложность настройки nginx
- ❌ Необходимость sudo для всех операций