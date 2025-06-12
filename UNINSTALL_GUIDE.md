# 🗑️ Руководство по удалению Toyota Dashboard

## 🚀 Быстрое удаление

### Одна команда
```bash
curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/uninstall.sh | sudo bash
```

### Или локально
```bash
cd /opt/toyota-dashboard
sudo ./uninstall.sh
```

## 🔒 Безопасность удаления

### Двойное подтверждение
1. **Первое**: Введите `yes` для подтверждения
2. **Второе**: Введите `DELETE` для окончательного подтверждения

### Предупреждения
- ⚠️ **Все данные будут потеряны** (credentials, история поездок)
- ⚠️ **Действие необратимо** - нужна будет переустановка
- ⚠️ **Требуются права root** - используйте `sudo`

## 📋 Что удаляется

### Сервисы и процессы
- ✅ **toyota-dashboard.service** - systemd сервис
- ✅ **Автозапуск** - отключается из systemctl
- ✅ **Активные процессы** - завершаются корректно

### Файлы и директории
- ✅ **/opt/toyota-dashboard** - основные файлы проекта
- ✅ **/var/log/toyota-dashboard** - все логи
- ✅ **/tmp/toyota-dashboard** - временные файлы
- ✅ **Домашняя директория пользователя toyota**

### Конфигурации
- ✅ **/etc/nginx/sites-available/toyota-dashboard** - конфигурация nginx
- ✅ **/etc/nginx/sites-enabled/toyota-dashboard** - активный сайт
- ✅ **/etc/systemd/system/toyota-dashboard.service** - файл сервиса

### Пользователи и группы
- ✅ **Пользователь toyota** - удаляется полностью
- ✅ **Группа toyota** - удаляется если существует
- ✅ **Все процессы пользователя** - завершаются

### Сетевые настройки
- ✅ **UFW правила** - порты 2025, 80, 443
- ✅ **iptables правила** - если UFW не используется
- ✅ **nginx reload** - применение изменений

## 🔄 Частичное удаление

### Только остановить сервис
```bash
sudo systemctl stop toyota-dashboard
sudo systemctl disable toyota-dashboard
```

### Только удалить nginx конфигурацию
```bash
sudo rm -f /etc/nginx/sites-enabled/toyota-dashboard
sudo rm -f /etc/nginx/sites-available/toyota-dashboard
sudo systemctl reload nginx
```

### Только удалить файлы (оставить сервис)
```bash
sudo rm -rf /opt/toyota-dashboard
sudo rm -rf /var/log/toyota-dashboard
```

### Только удалить пользователя
```bash
sudo pkill -u toyota
sudo userdel -r toyota
sudo groupdel toyota
```

## 📊 Отчет об удалении

### Автоматический отчет
Скрипт создает отчет в `/tmp/toyota-dashboard-removal-YYYYMMDD_HHMMSS.log`

### Содержимое отчета
```
Toyota Dashboard - Отчет об удалении
=====================================
Дата: 2024-01-15 14:30:25
Пользователь: root
Система: Linux raspberrypi 6.1.0-rpi4-rpi-v8 #1 SMP PREEMPT Debian

Удаленные компоненты:
✅ Сервис toyota-dashboard
✅ Файлы проекта (/opt/toyota-dashboard)
✅ Пользователь toyota
✅ Конфигурация nginx
✅ Логи (/var/log/toyota-dashboard)
✅ Правила файрвола
✅ Временные файлы

Статус: Удаление завершено успешно
```

## 🔧 Устранение проблем

### Если скрипт не запускается
```bash
# Проверить права
ls -la uninstall.sh

# Добавить права выполнения
chmod +x uninstall.sh

# Запустить с правами root
sudo ./uninstall.sh
```

### Если остались файлы
```bash
# Найти все файлы toyota
sudo find / -name "*toyota*" -type f 2>/dev/null

# Найти все процессы toyota
ps aux | grep toyota

# Принудительно завершить процессы
sudo pkill -9 -u toyota
```

### Если nginx не перезагружается
```bash
# Проверить конфигурацию
sudo nginx -t

# Принудительно перезапустить
sudo systemctl restart nginx

# Проверить статус
sudo systemctl status nginx
```

## 🔄 Переустановка

### После удаления
```bash
# Полная переустановка
curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/install.sh | sudo bash
```

### Сохранение настроек
Если хотите сохранить настройки перед удалением:
```bash
# Создать резервную копию
sudo cp /opt/toyota-dashboard/config.yaml ~/toyota-config-backup.yaml

# После переустановки восстановить
sudo cp ~/toyota-config-backup.yaml /opt/toyota-dashboard/config.yaml
sudo chown toyota:toyota /opt/toyota-dashboard/config.yaml
sudo systemctl restart toyota-dashboard
```

## ❓ Часто задаваемые вопросы

### Q: Можно ли отменить удаление?
**A:** Нет, удаление необратимо. Нужна полная переустановка.

### Q: Сохранятся ли мои Toyota credentials?
**A:** Нет, все данные удаляются. Сделайте резервную копию config.yaml.

### Q: Удалится ли nginx полностью?
**A:** Нет, удаляется только конфигурация Toyota Dashboard.

### Q: Что делать если удаление прервалось?
**A:** Запустите скрипт повторно - он безопасно обработает частично удаленные компоненты.

### Q: Можно ли удалить только веб-интерфейс?
**A:** Да, используйте частичное удаление nginx конфигурации.

---

**Удаление выполнено безопасно и полностью!** 🗑️✨