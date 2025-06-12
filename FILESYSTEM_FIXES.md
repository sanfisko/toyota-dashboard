# Исправления файловой системы только для чтения

## Проблема
Приложение Toyota Dashboard пыталось создавать файлы и директории в рабочей директории (`/opt/toyota-dashboard`), которая находится на файловой системе только для чтения.

## Решение
Все пути перенесены в системные директории с правами записи:

### Изменения в app.py
- Добавлены константы для базовых директорий:
  - `APP_DIR = '/opt/toyota-dashboard'` (только чтение)
  - `LOG_DIR = '/var/log/toyota-dashboard'` (запись)
  - `DATA_DIR = '/var/lib/toyota-dashboard'` (запись)

### Перенесенные пути
1. **Логи**: `/var/log/toyota-dashboard/app.log`
2. **Данные**: `/var/lib/toyota-dashboard/data/`
3. **Конфигурация**: `/opt/toyota-dashboard/config.yaml`
4. **Статические файлы**: `/opt/toyota-dashboard/static/`
5. **Резервные копии**: `/var/lib/toyota-dashboard/backups/`

### Обновленные файлы
- `app.py` - все пути к файлам и директориям
- `config.example.yaml` - пути в конфигурации

### Директории, создаваемые install.sh
```bash
/opt/toyota-dashboard              # Приложение (только чтение)
/var/log/toyota-dashboard          # Логи (запись)
/var/lib/toyota-dashboard/data     # База данных (запись)
/var/lib/toyota-dashboard/backups  # Резервные копии (запись)
```

## Результат
- ✅ Приложение больше не пытается создавать файлы в рабочей директории
- ✅ Все данные сохраняются в системных директориях с правами записи
- ✅ Логи записываются в `/var/log/toyota-dashboard/`
- ✅ База данных создается в `/var/lib/toyota-dashboard/data/`
- ✅ Конфигурация читается из `/opt/toyota-dashboard/config.yaml`

## Для обновления
Запустите переустановку:
```bash
sudo bash install.sh --reinstall
```

Скрипт автоматически создаст все необходимые директории с правильными правами доступа.