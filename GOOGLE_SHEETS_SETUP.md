# Настройка интеграции с Google Sheets

## Назначение

Система автоматически отправляет данные о статусе работы сотрудников в Google Таблицы:
- Дата и время скриншота
- Имя сотрудника
- Статус (Работа/Личное)
- Детали (обнаруженные приложения)

## Шаг 1: Создание Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)

2. **Создайте новый проект** (или выберите существующий):
   - Нажмите на выпадающий список проектов вверху
   - Нажмите "New Project"
   - Введите имя (например, "Screenshot Analytics")
   - Нажмите "Create"

3. **Включите Google Sheets API**:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Google Sheets API"
   - Нажмите "Enable"

4. **Создайте Service Account**:
   - Перейдите в "IAM & Admin" → "Service Accounts"
   - Нажмите "Create Service Account"
   - Введите имя (например, "sheets-bot")
   - Нажмите "Create and Continue"
   - Пропустите назначение роли (или выберите "Viewer")
   - Нажмите "Done"

5. **Создайте JSON ключ**:
   - Найдите созданный Service Account в списке
   - Нажмите на него
   - Перейдите на вкладку "Keys"
   - Нажмите "Add Key" → "Create new key"
   - Выберите "JSON"
   - Нажмите "Create"
   - JSON файл автоматически скачается

6. **Переименуйте файл** в `service_account.json` и переместите в `config/` папку проекта:
   ```powershell
   mkdir config
   move путь_к_скачанному_файлу config/service_account.json
   ```

## Шаг 2: Создание Google Таблицы

1. **Создайте новую таблицу**:
   - Перейдите в [Google Sheets](https://sheets.google.com)
   - Нажмите "Blank" (Пустой)
   - Введите имя (например, "Скриншоты сотрудников")

2. **Скопируйте ID таблицы**:
   - URL таблицы выглядит так: `https://docs.google.com/spreadsheets/d/ABC123xyz/edit`
   - ID это часть между `/d/` и `/edit`: `ABC123xyz`

3. **Поделитесь таблицей с Service Account**:
   - Нажмите кнопку "Share" (Поделиться)
   - Скопируйте email Service Account из JSON файла (поле `client_email`)
   - Выставьте права "Editor" (Редактор)
   - Нажмите "Share"

## Шаг 3: Настройка конфигурации

Откройте `.env` файл и настройте переменные:

```env
# Путь к JSON ключу Service Account (внутри контейнера)
GOOGLE_SERVICE_ACCOUNT_FILE=/app/config/service_account.json

# ID вашей Google Таблицы
GOOGLE_SPREADSHEET_ID=ABC123xyz

# Название листа (по умолчанию 'Лист1')
GOOGLE_SHEET_NAME=Лист1
```

В `docker-compose.yml` убедитесь что файл mounted:

```yaml
services:
  ocr-analyzer:
    # ...
    volumes:
      - ./config/service_account.json:/app/config/service_account.json:ro
```

## Шаг 4: Проверка работы

1. **Запустите систему**:
   ```powershell
   docker-compose up -d
   ```

2. **Проверьте логи**:
   ```powershell
   docker-compose logs ocr-analyzer
   ```

3. **Проверьте таблицу**:
   - Откройте Google Таблицу
   - После обработки скриншотов данные должны появиться автоматически
   - Формат: `Дата | Время | Сотрудник | Статус | Детали`

Пример:
```
| 2024-01-15 | 09:30 | Иванов | Работа | Рабочие: excel, word |
| 2024-01-15 | 10:15 | Петров | Личное | Личные: youtube, vk  |
```

## 🐛 Troubleshooting

### Ошибка: "Permission denied"
- Убедитесь что вы поделились таблицей с email Service Account
- Проверьте что Service Account имеет права Editor

### Ошибка: "Invalid API key"
- Проверьте что JSON файл корректный
- Убедитесь что путь в `.env` правильный

### Ошибка: "Spreadsheet not found"
- Проверьте ID таблицы
- Убедитесь что таблица доступна по ссылке с Service Account

### Данные не отправляются
- Проверьте логи OCR analyzer на наличие ошибок
- Убедитесь что включен Google Sheets API в проекте

## 🔒 Безопасность

- Никогда не коммитьте `service_account.json` в Git
- Добавьте в `.gitignore`:
  ```
  config/
  *.json
  .env
  ```
- Используйте отдельные Service Account для разных сред (dev/prod)
- Регулярно вращайте ключи Service Account

## 📊 Формат данных в Google Sheets

| Колонка | Описание | Пример |
|---------|----------|--------|
| Дата | Дата скриншота (YYYY-MM-DD) | 2024-01-15 |
| Время | Время скриншота (HH:MM) | 09:30 |
| Сотрудник | Имя сотрудника | Иванов |
| Статус | Категория активности | Работа / Личное |
| Детали | Обнаруженные приложения | Рабочие: excel, word |

## 🔄 Частота отправки

Данные отправляются пакетно после каждой обработки батча скриншотов (по умолчанию каждые 60 секунд).

## 💡 Советы

1. **Фильтрация данных**: В Google Sheets используйте фильтры для анализа по сотруднику или дате
2. **Уведомления**: Настройте уведомления об изменениях в таблице
3. **Визуализация**: Используйте встроенные графики Google Sheets для отчетности
4. **Экспорт**: Экспортируйте данные в Excel/PDF для финальных отчетов

## 📞 Поддержка

При проблемах проверьте:
1. Логи контейнера: `docker-compose logs ocr-analyzer`
2. Доступность API: [Sheets API Explorer](https://developers.google.com/sheets/api/guides/concepts)
3. Документация Google: [Sheets API Quickstart](https://developers.google.com/sheets/api/quickstart/python)
