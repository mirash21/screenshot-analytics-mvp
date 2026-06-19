# Конфигурация дашборда
import os

# Путь к базе данных
DB_PATH = os.environ.get('DB_PATH', '/app/storage/database/analytics.db')

# Настройки авторизации
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
AUTH_SALT = os.environ.get('AUTH_SALT', 'default_salt_change_me')

# Логирование
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
