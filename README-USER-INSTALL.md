# Toyota Dashboard - Установка под пользователем

## Обзор

Новый способ установки Toyota Dashboard, который работает под текущим пользователем вместо создания отдельного системного пользователя. Это решает проблемы с правами доступа и упрощает управление.

## Преимущества пользовательской установки

✅ **Нет проблем с правами доступа** - все файлы принадлежат вашему пользователю  
✅ **Простое управление** - используйте стандартные команды systemctl --user  
✅ **Безопасность** - приложение работает с правами обычного пользователя  
✅ **Легкое обновление** - простые git pull и pip install  
✅ **Чистое удаление** - все файлы в домашней директории  

## Быстрая установка

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh" | bash
```

Или с автоматическим подтверждением:

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh" | bash -s -- -y
```

## Что устанавливается

### Структура файлов

```
~/toyota-dashboard/                    # Основная установка
├── app.py                            # Главное приложение
├── venv/                             # Виртуальное окружение Python
├── static/                           # Веб-интерфейс
├── start.sh                          # Скрипт запуска
├── stop.sh                           # Скрипт остановки
└── update.sh                         # Скрипт обновления

~/.config/toyota-dashboard/            # Конфигурация
└── config.yaml                       # Файл настроек

~/.local/share/toyota-dashboard/       # Данные
├── toyota.db                         # База данных
├── logs/                             # Логи приложения
└── backups/                          # Резервные копии

~/.cache/toyota-dashboard/             # Кэш
└── ...                               # Временные файлы

~/.config/systemd/user/                # Systemd сервис
└── toyota-dashboard.service          # Файл сервиса
```

## Настройка

### 1. Редактирование конфигурации

```bash
nano ~/.config/toyota-dashboard/config.yaml
```

Добавьте ваши данные Toyota:

```yaml
toyota:
  username: "your-email@example.com"  # Ваш email от Toyota Connected
  password: "your-password"           # Ваш пароль
  vin: "YOUR-VIN-NUMBER"             # VIN номер автомобиля
  region: "europe"                    # Регион: europe, north_america, asia
```

### 2. Запуск сервиса

```bash
systemctl --user restart toyota-dashboard
```

## Управление сервисом

### Systemd команды

```bash
# Запуск
systemctl --user start toyota-dashboard

# Остановка
systemctl --user stop toyota-dashboard

# Перезапуск
systemctl --user restart toyota-dashboard

# Статус
systemctl --user status toyota-dashboard

# Включить автозапуск
systemctl --user enable toyota-dashboard

# Отключить автозапуск
systemctl --user disable toyota-dashboard

# Просмотр логов
journalctl --user -u toyota-dashboard -f
```

### Скрипты управления

```bash
# Запуск в консоли (для отладки)
~/toyota-dashboard/start.sh

# Остановка всех процессов
~/toyota-dashboard/stop.sh

# Обновление до последней версии
~/toyota-dashboard/update.sh
```

## Доступ к приложению

- **Локально**: http://localhost:2025
- **По сети**: http://YOUR-IP:2025
- **Настройка**: http://YOUR-IP:2025/setup

## Логи и диагностика

### Просмотр логов

```bash
# Системные логи
journalctl --user -u toyota-dashboard -f

# Логи приложения
tail -f ~/.local/share/toyota-dashboard/logs/app.log

# Все логи сразу
tail -f ~/.local/share/toyota-dashboard/logs/app.log & journalctl --user -u toyota-dashboard -f
```

### Диагностика проблем

```bash
# Проверка статуса
systemctl --user status toyota-dashboard

# Проверка процессов
ps aux | grep toyota-dashboard

# Проверка портов
netstat -tlnp | grep 2025

# Тест конфигурации
cd ~/toyota-dashboard && source venv/bin/activate && python -c "import yaml; print(yaml.safe_load(open('~/.config/toyota-dashboard/config.yaml')))"
```

## Обновление

### Автоматическое обновление

```bash
~/toyota-dashboard/update.sh
systemctl --user restart toyota-dashboard
```

### Ручное обновление

```bash
cd ~/toyota-dashboard
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
systemctl --user restart toyota-dashboard
```

## Резервное копирование

### Создание резервной копии

```bash
# Полная резервная копия
tar -czf ~/toyota-dashboard-backup-$(date +%Y%m%d).tar.gz \
  ~/.config/toyota-dashboard \
  ~/.local/share/toyota-dashboard \
  ~/toyota-dashboard

# Только данные и конфигурация
tar -czf ~/toyota-dashboard-data-$(date +%Y%m%d).tar.gz \
  ~/.config/toyota-dashboard \
  ~/.local/share/toyota-dashboard
```

### Восстановление

```bash
# Остановить сервис
systemctl --user stop toyota-dashboard

# Восстановить файлы
tar -xzf ~/toyota-dashboard-backup-YYYYMMDD.tar.gz -C ~/

# Запустить сервис
systemctl --user start toyota-dashboard
```

## Удаление

### Автоматическое удаление

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall-user.sh" | bash
```

### Ручное удаление

```bash
# Остановить и отключить сервис
systemctl --user stop toyota-dashboard
systemctl --user disable toyota-dashboard

# Удалить файлы сервиса
rm -f ~/.config/systemd/user/toyota-dashboard.service
systemctl --user daemon-reload

# Удалить приложение
rm -rf ~/toyota-dashboard

# Удалить данные (опционально)
rm -rf ~/.config/toyota-dashboard
rm -rf ~/.local/share/toyota-dashboard
rm -rf ~/.cache/toyota-dashboard
```

## Миграция со старой установки

Если у вас уже установлен Toyota Dashboard с системным пользователем `toyota`:

### 1. Сохранение данных

```bash
# Создать резервную копию конфигурации
sudo cp /opt/toyota-dashboard/config.yaml ~/config-backup.yaml
sudo chown $USER:$USER ~/config-backup.yaml

# Создать резервную копию базы данных (если есть)
sudo cp /var/lib/toyota-dashboard/data/toyota.db ~/toyota-backup.db 2>/dev/null || true
sudo chown $USER:$USER ~/toyota-backup.db 2>/dev/null || true
```

### 2. Удаление старой установки

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh" | sudo bash
```

### 3. Установка новой версии

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh" | bash
```

### 4. Восстановление данных

```bash
# Восстановить конфигурацию
cp ~/config-backup.yaml ~/.config/toyota-dashboard/config.yaml

# Восстановить базу данных (если есть)
cp ~/toyota-backup.db ~/.local/share/toyota-dashboard/toyota.db 2>/dev/null || true

# Перезапустить сервис
systemctl --user restart toyota-dashboard
```

## Устранение неполадок

### Сервис не запускается

```bash
# Проверить логи
journalctl --user -u toyota-dashboard -n 50

# Проверить конфигурацию
cd ~/toyota-dashboard && source venv/bin/activate && python app.py
```

### Проблемы с правами доступа

```bash
# Исправить права на файлы
chmod -R u+rw ~/.config/toyota-dashboard
chmod -R u+rw ~/.local/share/toyota-dashboard
chmod +x ~/toyota-dashboard/*.sh
```

### Порт занят

```bash
# Найти процесс, использующий порт 2025
sudo netstat -tlnp | grep 2025
sudo lsof -i :2025

# Изменить порт в конфигурации
nano ~/.config/toyota-dashboard/config.yaml
# Измените server.port на другое значение
```

### Проблемы с зависимостями

```bash
cd ~/toyota-dashboard
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## Поддержка

- **GitHub Issues**: https://github.com/sanfisko/toyota-dashboard/issues
- **Документация**: https://github.com/sanfisko/toyota-dashboard
- **Логи**: Всегда прикладывайте логи при сообщении о проблемах

## Сравнение с системной установкой

| Аспект | Системная установка | Пользовательская установка |
|--------|-------------------|---------------------------|
| Права доступа | Проблемы с `/home/toyota` | ✅ Нет проблем |
| Управление | `sudo systemctl` | `systemctl --user` |
| Безопасность | Системный пользователь | ✅ Пользовательские права |
| Обновление | Требует sudo | ✅ Простое |
| Удаление | Системные файлы | ✅ Только домашняя папка |
| Автозапуск | ✅ При загрузке системы | При входе пользователя |
| Изоляция | ✅ Отдельный пользователь | Текущий пользователь |

## Заключение

Пользовательская установка рекомендуется для большинства случаев использования, особенно на персональных Raspberry Pi. Она проще в управлении и не имеет проблем с правами доступа.

Системная установка может быть предпочтительна только в случаях, когда нужен запуск сервиса до входа пользователя в систему или строгая изоляция приложения.