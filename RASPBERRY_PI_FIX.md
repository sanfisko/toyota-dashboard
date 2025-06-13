# Исправление ошибки "Read-only file system" на Raspberry Pi

## Проблема
При запуске Toyota Dashboard на Raspberry Pi возникает ошибка:
```
[Errno 30] Read-only file system: '.cache'
```

## Причина
Приложение пытается создать кэш-директорию в текущей рабочей директории, но файловая система смонтирована в режиме только для чтения.

## Решение

### Вариант 1: Обновление до последней версии
Скачайте и установите последнюю версию приложения, которая уже содержит исправления:

```bash
cd /opt/toyota-dashboard
sudo systemctl stop toyota-dashboard
sudo git pull origin main
sudo systemctl start toyota-dashboard
```

### Вариант 2: Ручное исправление

1. **Остановите сервис:**
```bash
sudo systemctl stop toyota-dashboard
```

2. **Создайте кэш-директорию:**
```bash
sudo mkdir -p /home/sanfisko/.cache/toyota-dashboard
sudo chown -R sanfisko:sanfisko /home/sanfisko/.cache
```

3. **Обновите systemd unit файл:**
```bash
sudo nano /etc/systemd/system/toyota-dashboard.service
```

Добавьте следующие строки в секцию `[Service]`:
```ini
Environment=HOME=/home/sanfisko
Environment=XDG_CACHE_HOME=/home/sanfisko/.cache
Environment=HTTPX_CACHE_DIR=/home/sanfisko/.cache/toyota-dashboard
ExecStartPre=/bin/mkdir -p /home/sanfisko/.cache/toyota-dashboard
```

4. **Перезагрузите systemd и запустите сервис:**
```bash
sudo systemctl daemon-reload
sudo systemctl start toyota-dashboard
```

### Вариант 3: Изменение рабочей директории

Если проблема продолжается, измените рабочую директорию в systemd unit файле:

```bash
sudo nano /etc/systemd/system/toyota-dashboard.service
```

Измените строку `WorkingDirectory`:
```ini
WorkingDirectory=/home/sanfisko
```

## Проверка исправления

После применения исправления проверьте статус сервиса:

```bash
sudo systemctl status toyota-dashboard
sudo journalctl -u toyota-dashboard -f
```

Ошибка "Read-only file system" больше не должна появляться в логах.

## Дополнительные рекомендации

1. **Убедитесь, что файловая система не в режиме только для чтения:**
```bash
mount | grep "ro,"
```

2. **Если система в режиме только для чтения, переключите в режим записи:**
```bash
sudo mount -o remount,rw /
```

3. **Проверьте свободное место на диске:**
```bash
df -h
```

4. **Убедитесь, что пользователь имеет права на запись в домашнюю директорию:**
```bash
ls -la /home/sanfisko/
```