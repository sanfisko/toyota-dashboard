# 🚗 Toyota Dashboard - Быстрый старт (пользовательская установка)

## 🎯 Решение проблем с правами доступа

Вместо создания системного пользователя `toyota`, новый способ установки работает под вашим текущим пользователем. Это полностью решает проблемы с правами доступа!

## ⚡ Быстрая установка

```bash
# Удалите старую установку (если есть)
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh" | sudo bash

# Установите новую версию под вашим пользователем
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install-user.sh" | bash
```

## 🔧 Настройка

```bash
# Отредактируйте конфигурацию
nano ~/.config/toyota-dashboard/config.yaml

# Добавьте ваши данные Toyota:
# username: "your-email@example.com"
# password: "your-password"  
# vin: "YOUR-VIN-NUMBER"

# Перезапустите сервис
systemctl --user restart toyota-dashboard
```

## 🎮 Управление

```bash
# Запуск
systemctl --user start toyota-dashboard

# Остановка  
systemctl --user stop toyota-dashboard

# Статус
systemctl --user status toyota-dashboard

# Логи
journalctl --user -u toyota-dashboard -f
```

## 🌐 Доступ

- **Локально**: http://localhost:2025
- **По сети**: http://YOUR-IP:2025

## ✅ Преимущества

- ✅ **Нет проблем с правами доступа**
- ✅ **Простое управление** 
- ✅ **Безопасность** - работа под обычным пользователем
- ✅ **Легкое обновление** - `~/toyota-dashboard/update.sh`
- ✅ **Чистое удаление** - все в домашней папке

## 📚 Подробная документация

Смотрите [README-USER-INSTALL.md](README-USER-INSTALL.md) для полной документации.

---

**Теперь Toyota Dashboard будет работать стабильно без проблем с правами доступа! 🎉**