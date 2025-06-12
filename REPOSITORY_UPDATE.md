# 🔄 Обновление репозитория toyota-dashboard

## ✅ Что сделано

### 🏷️ Переименование репозитория
- **Старое название**: `pytoyoda`
- **Новое название**: `toyota-dashboard`
- **URL**: https://github.com/tifainechevaliermuzpub/toyota-dashboard

### 📝 Обновленная документация
- ✅ Новый главный README.md с полным описанием проекта
- ✅ Обновлены все ссылки на новый репозиторий
- ✅ Исправлены команды установки
- ✅ Добавлены визуальные примеры интерфейса

### 🔗 Исправленные ссылки
- ✅ Установочный скрипт: `curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/install.sh | sudo bash`
- ✅ GitHub Issues: https://github.com/tifainechevaliermuzpub/toyota-dashboard/issues
- ✅ Клонирование: `git clone https://github.com/tifainechevaliermuzpub/toyota-dashboard.git`

## 🚀 Новые возможности

### 🌐 Веб-настройка
- Удобная форма для ввода Toyota credentials
- Тестирование подключения перед сохранением
- Автоматическая проверка VIN номера
- Смена порта через веб-интерфейс

### 🔧 Гибкая конфигурация
- Настраиваемый порт (по умолчанию 2025)
- Автоматическое обновление nginx
- Совместимость с другими сервисами

### 📱 Улучшенный интерфейс
- Отзывчивый дизайн для мобильных устройств
- Темная тема
- PWA поддержка для iPhone
- Визуальная обратная связь

## 📋 Инструкции для пользователей

### Новая установка
```bash
# Одна команда для полной установки на Raspberry Pi
curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/install.sh | sudo bash
```

### Обновление существующей установки
```bash
# Перейти в директорию проекта
cd /opt/toyota-dashboard

# Обновить код
sudo -u toyota git pull origin main

# Перезапустить сервис
sudo systemctl restart toyota-dashboard
```

### Настройка через веб-интерфейс
1. Откройте `http://IP_RASPBERRY_PI/setup`
2. Заполните форму с вашими Toyota credentials
3. Нажмите "Проверить подключение"
4. Сохраните настройки
5. Готово!

## 🎯 Следующие шаги

1. **Установите на Raspberry Pi** используя новую команду
2. **Настройте через веб-интерфейс** - больше не нужно редактировать файлы
3. **Добавьте на главный экран iPhone** как PWA приложение
4. **Наслаждайтесь** полным контролем над вашим Toyota!

## 📞 Поддержка

- **GitHub Issues**: https://github.com/tifainechevaliermuzpub/toyota-dashboard/issues
- **Документация**: [TOYOTA_CHR_PHEV_DASHBOARD.md](TOYOTA_CHR_PHEV_DASHBOARD.md)
- **Telegram**: @toyota_chr_phev_ru

---

**Проект готов к использованию!** 🚗✨