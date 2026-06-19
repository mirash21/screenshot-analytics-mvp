# Конфигурация

В эту папку помещаются чувствительные конфигурационные файлы:

## service_account.json

JSON ключ Service Account для интеграции с Google Sheets.

### Как получить:

1. Следуйте инструкции в [GOOGLE_SHEETS_SETUP.md](../GOOGLE_SHEETS_SETUP.md)
2. Скачайте JSON ключ из Google Cloud Console
3. Поместите файл в эту папку

### Важно:

- ⚠️ **Никогда не коммитьте этот файл в Git!**
- Файл автоматически игнорируется через .gitignore
- Используйте разные ключи для dev/prod сред
