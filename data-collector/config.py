# Конфигурация путей для модуля сбора данных
import os

# Пути внутри контейнера
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/app/incoming')
SCREENSHOTS_DIR = os.environ.get('SCREENSHOTS_DIR', '/app/storage/screenshots')
DB_PATH = os.environ.get('DB_PATH', '/app/storage/database/analytics.db')

# Интервал сканирования (в секундах)
SCAN_INTERVAL_SECONDS = int(os.environ.get('SCAN_INTERVAL_SECONDS', '300'))

# Логирование
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
