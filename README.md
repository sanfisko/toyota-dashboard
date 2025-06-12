# 🚗📊 Toyota Dashboard

**Персональный сервер для мониторинга и управления Toyota автомобилями с веб-интерфейсом для iPhone**

[![GitHub Stars](https://img.shields.io/github/stars/tifainechevaliermuzpub/toyota-dashboard?style=social)](https://github.com/tifainechevaliermuzpub/toyota-dashboard)
[![GitHub Issues](https://img.shields.io/github/issues/tifainechevaliermuzpub/toyota-dashboard)](https://github.com/tifainechevaliermuzpub/toyota-dashboard/issues)
[![License](https://img.shields.io/github/license/tifainechevaliermuzpub/toyota-dashboard)](LICENSE)

## 🎯 Что это такое?

Toyota Dashboard - это полноценное решение для владельцев Toyota (особенно C-HR PHEV), которое превращает ваш Raspberry Pi в персональный центр управления автомобилем.

### ✨ Основные возможности

- 📊 **Мониторинг в реальном времени**: батарея, топливо, местоположение
- 🎮 **Дистанционное управление**: замки, двигатель, климат, поиск авто
- 📱 **iPhone-оптимизированный интерфейс**: PWA поддержка, темная тема
- 📈 **Детальная аналитика PHEV**: эффективность, экономия, статистика
- 🌐 **Веб-настройка**: удобная форма для ввода credentials
- 🔧 **Гибкая конфигурация**: настраиваемые порты, автоматическая установка

## 🚀 Быстрый старт

### Автоматическая установка на Raspberry Pi
```bash
curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/install.sh | sudo bash
```

### Настройка через веб-интерфейс
1. Откройте `http://IP_RASPBERRY_PI/setup`
2. Введите ваши Toyota Connected credentials
3. Протестируйте подключение
4. Сохраните настройки
5. Готово! 🎉

## 📱 Скриншоты

### Главный дашборд
```
┌─────────────────────────┐
│  🚗 Toyota C-HR PHEV    │
├─────────────────────────┤
│  🔋 85%  ⛽ 320км       │
│  📍 Дом  🔒 Заблокирован │
├─────────────────────────┤
│  [🔓] [🚗] [❄️] [📍]    │
│  Открыть Запуск Климат Найти │
├─────────────────────────┤
│  📊 За сегодня:         │
│  🔋 25км (электро)      │
│  ⛽ 15км (бензин)       │
│  💰 Экономия: 180₽     │
└─────────────────────────┘
```

### Страница настройки
```
┌─────────────────────────┐
│  ⚙️ Настройка Toyota    │
├─────────────────────────┤
│  📧 Email: [_________]  │
│  🔒 Пароль: [_______]  │
│  🚗 VIN: [___________]  │
│  🌍 Регион: [Европа ▼] │
│  🌐 Порт: [2025_____]  │
├─────────────────────────┤
│  [🔍 Проверить подключение] │
│  [💾 Сохранить настройки]   │
└─────────────────────────┘
```

## 🛠️ Структура проекта

```
toyota-dashboard/
├── pytoyoda/                    # Библиотека для Toyota API
│   ├── api.py                   # Основной API клиент
│   ├── models/                  # Модели данных
│   └── utils/                   # Утилиты
├── toyota_dashboard_server/     # Веб-сервер дашборда
│   ├── app.py                   # FastAPI приложение
│   ├── database.py              # Работа с базой данных
│   ├── models.py                # Модели сервера
│   ├── static/                  # Веб-интерфейс
│   │   ├── index.html           # Главная страница
│   │   └── setup.html           # Страница настройки
│   ├── config.example.yaml      # Пример конфигурации
│   ├── requirements.txt         # Python зависимости
│   └── install.sh               # Установочный скрипт
├── TOYOTA_CHR_PHEV_DASHBOARD.md # Подробная документация
└── README.md                    # Этот файл
```

## 🎮 Возможности управления

### Доступные команды
- 🔒 **Замки**: блокировка/разблокировка дверей и багажника
- 🚗 **Двигатель**: дистанционный запуск для прогрева
- ❄️ **Климат**: управление кондиционером и обогревом
- 💡 **Освещение**: включение фар и аварийной сигнализации
- 📍 **Поиск**: звуковой сигнал и мигание фар
- 🪟 **Окна**: управление стеклоподъемниками (зависит от модели)

### Мониторинг
- 🔋 **Батарея**: уровень заряда HV батареи
- ⛽ **Топливо**: текущий запас хода
- 📍 **Местоположение**: GPS координаты и адрес
- 📊 **Статистика**: пробег, расход, эффективность
- 🕐 **История**: поездки, команды, уведомления

## 📊 API Endpoints

### Статус автомобиля
```bash
GET /api/vehicle/status          # Текущий статус
GET /api/vehicle/location        # Местоположение
GET /api/stats/phev?period=week  # Статистика PHEV
```

### Управление
```bash
POST /api/vehicle/lock           # Заблокировать
POST /api/vehicle/unlock         # Разблокировать
POST /api/vehicle/start          # Запустить двигатель
POST /api/vehicle/climate        # Управление климатом
```

### Конфигурация
```bash
GET /api/config                  # Текущие настройки
POST /api/test-connection        # Тест подключения
POST /api/save-config            # Сохранить настройки
```

## 🔧 Системные требования

### Рекомендуемая конфигурация
- **Raspberry Pi 4B** (4GB RAM)
- **MicroSD карта** 32GB+ (Class 10)
- **Raspbian OS Lite** (64-bit)
- **Стабильное интернет-соединение**

### Поддерживаемые автомобили
- ✅ **Toyota C-HR PHEV** (основная поддержка)
- ✅ **Toyota Prius PHEV**
- ✅ **Toyota RAV4 PHEV**
- ⚠️ **Другие Toyota Connected** (базовая поддержка)

## 🌍 Доступ

### Локальная сеть
```bash
# Через nginx (рекомендуется)
http://192.168.1.XXX

# Прямой доступ
http://192.168.1.XXX:2025

# Настройка
http://192.168.1.XXX/setup
```

### Внешний доступ
```bash
# Cloudflare Tunnel (бесплатно)
cloudflared tunnel --url http://localhost:80

# ngrok
ngrok http 80
```

## 🔒 Безопасность

- 🛡️ **Локальное хранение** данных
- 🔐 **Шифрование** паролей
- 🚫 **Нет облачных сервисов**
- 🔥 **Файрвол** настроен автоматически
- 📝 **Логирование** всех действий

## 📚 Документация

- 📖 **[Полная документация](TOYOTA_CHR_PHEV_DASHBOARD.md)** - подробное руководство
- 💡 **[Креативные идеи](CREATIVE_IDEAS.md)** - 23 идеи для развития
- 🔒 **[Безопасность](SECURITY_IMPROVEMENTS.md)** - рекомендации по защите
- 🏗️ **[Архитектура](ARCHITECTURE_IMPROVEMENTS.md)** - технические улучшения

## 🗑️ Удаление

### Полное удаление
```bash
# Одна команда для полного удаления
curl -sSL https://raw.githubusercontent.com/tifainechevaliermuzpub/toyota-dashboard/main/toyota_dashboard_server/uninstall.sh | sudo bash
```

### Что удаляется
- ✅ Сервис и автозапуск
- ✅ Все файлы проекта
- ✅ Пользователь toyota
- ✅ Конфигурация nginx
- ✅ База данных и логи
- ✅ Правила файрвола

**Безопасно**: двойное подтверждение + отчет об удалении

## 🆘 Поддержка

### Сообщество
- 🐛 **[GitHub Issues](https://github.com/tifainechevaliermuzpub/toyota-dashboard/issues)** - баги и предложения
- 💬 **Telegram**: @toyota_chr_phev_ru
- 📧 **Email**: support@toyota-dashboard.pro

### Частые проблемы
```bash
# Проверка статуса сервиса
sudo systemctl status toyota-dashboard

# Просмотр логов
sudo journalctl -u toyota-dashboard -f

# Перезапуск сервиса
sudo systemctl restart toyota-dashboard
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! 

1. 🍴 **Fork** репозитория
2. 🌿 **Создайте** ветку для новой функции
3. 💻 **Внесите** изменения
4. 🧪 **Протестируйте** код
5. 📤 **Создайте** Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- **[@DurgNomis-drol](https://github.com/DurgNomis-drol)** - за оригинальную библиотеку PyToyoda
- **[@calmjm](https://github.com/calmjm)** - за проект [tojota](https://github.com/calmjm/tojota)
- **Сообщество Toyota PHEV** - за тестирование и обратную связь

---

**Создано с ❤️ для владельцев Toyota** 🚗✨

*Превратите ваш автомобиль в умный подключенный девайс!*