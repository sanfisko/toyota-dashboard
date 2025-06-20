# 🚗 Toyota Dashboard

> Когда твоя Toyota умнее тебя, но ты все равно хочешь ею управлять

Простой веб-интерфейс для мониторинга и управления Toyota. Потому что кнопки в приложении Toyota слишком мелкие, а ты хочешь чувствовать себя хакером.

## 🎯 Что умеет

- **Показывает** сколько бензина осталось (чтобы не застрять на трассе)
- **Блокирует/разблокирует** двери (для тех, кто постоянно забывает)
- **Заводит** машину дистанционно (как в фильмах про шпионов)
- **Включает** кондиционер (чтобы не потеть в пробках)
- **Следит** за поездками (Big Brother, но полезный)

## 🚀 Установка

### Для ленивых (рекомендуется)
```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh" | sudo bash
```

### Для параноиков
```bash
git clone https://github.com/sanfisko/toyota-dashboard.git
cd toyota-dashboard
# Читаем код, убеждаемся что он не майнит биткоины
pip install -r requirements.txt
python app.py
```

## ⚙️ Настройка

После установки перейди на `http://твой-raspberry-pi:2025/setup` и введи свои данные Toyota Connected Services:
- Email от Toyota Connected
- Пароль
- VIN номер автомобиля

Система автоматически проверит подключение и сохранит настройки.

> ⚠️ **Важно:** Данные хранятся локально и используются только для подключения к Toyota API.

## 📱 Использование

1. Открой браузер
2. Иди на `http://твой-raspberry-pi:2025`
3. Наслаждайся контролем над машиной
4. Чувствуй себя Илоном Маском

## 🔧 Если что-то сломалось

### Машина не отвечает
- Проверь интернет (может быть, проблема не в коде)
- Убедись, что Toyota не обновила API (они любят это делать)
- Попробуй выключить и включить (работает в 90% случаев)

### Приложение падает
```bash
# Посмотри что случилось
sudo journalctl -u toyota-dashboard -f

# Если не помогло, переустанови
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/uninstall.sh" | sudo bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh" | sudo bash
```

### Raspberry Pi тормозит
- Купи Raspberry Pi 4 (или не жалуйся)
- Увеличь интервал обновления в настройках
- Отключи ненужные фичи

## 🤝 Помощь проекту

Нашел баг? Хочешь новую фичу? Добро пожаловать в [Issues](https://github.com/sanfisko/toyota-dashboard/issues).

Умеешь кодить? Pull requests приветствуются (но сначала убедись, что код работает).

## 🔧 Устранение неполадок

### Проблема с правами доступа "Permission denied"

Если вы видите ошибки типа `Permission denied: '/home/toyota'`, сначала проведите диагностику:

```bash
# Диагностика проблемы
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh" | sudo bash -s -- --diagnose

# Исправление прав доступа
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/install.sh" | sudo bash -s -- --fix-permissions
```

### Проверка статуса сервиса

```bash
# Статус сервиса
sudo systemctl status toyota-dashboard

# Логи в реальном времени
sudo journalctl -u toyota-dashboard -f

# Перезапуск сервиса
sudo systemctl restart toyota-dashboard
```

### Диагностика системы

Откройте в браузере: `http://ваш-ip/diagnostics.html` для проверки состояния системы.

## 📜 Лицензия

MIT - делай что хочешь, но если что-то сломается, это не наша вина.

## 🙏 Спасибо

- **[pytoyoda](https://github.com/pytoyoda/pytoyoda)** - за то, что разобрались с API Toyota
- **Toyota** - за то, что сделали API (хоть и не документировали его)
- **Всем тестерам** - за то, что находят баги быстрее нас

---

*Сделано с ☕ и небольшой долей безумия*