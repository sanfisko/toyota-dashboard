# 🚀 Быстрое исправление ошибки "Permission denied"

## Проблема
```
PermissionError: [Errno 13] Permission denied: '/home/toyota/.local/share/toyota-dashboard/logs/app.log'
```

## ⚡ Быстрое решение

Запустите одну команду для автоматического исправления:

```bash
curl -sSL "https://raw.githubusercontent.com/sanfisko/toyota-dashboard/main/fix_permissions.sh" | sudo bash
```

## 🔍 Что делает скрипт

1. ✅ Создает все необходимые директории
2. ✅ Устанавливает правильные права доступа
3. ✅ Копирует конфигурацию в безопасное место
4. ✅ Перезапускает сервис
5. ✅ Проверяет результат

## 📋 После исправления

1. **Проверьте статус сервиса:**
   ```bash
   sudo systemctl status toyota-dashboard
   ```

2. **Откройте веб-интерфейс:**
   ```
   http://ВАШ_IP_АДРЕС
   ```

3. **Используйте диагностику:**
   ```
   http://ВАШ_IP_АДРЕС/diagnostics
   ```

## 🆘 Если проблема остается

1. **Просмотрите логи:**
   ```bash
   sudo journalctl -u toyota-dashboard -f
   ```

2. **Запустите диагностику:**
   ```bash
   cd /opt/toyota-dashboard
   python3 test_paths.py
   ```

3. **Ручное исправление:**
   ```bash
   # Создать пользовательские директории
   sudo mkdir -p /home/toyota/.config/toyota-dashboard
   sudo mkdir -p /home/toyota/.local/share/toyota-dashboard/logs
   
   # Установить права
   sudo chown -R toyota:toyota /home/toyota/.config/toyota-dashboard
   sudo chown -R toyota:toyota /home/toyota/.local/share/toyota-dashboard
   
   # Перезапустить сервис
   sudo systemctl restart toyota-dashboard
   ```

## 💡 Дополнительная информация

- 📖 Подробная документация: `FIX_READONLY_FILESYSTEM.md`
- 🔧 Резюме изменений: `SUMMARY.md`
- 🧪 Тестирование: `test_paths.py`

---
**Все исправления полностью обратно совместимы и безопасны!** 🛡️