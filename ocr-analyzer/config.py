# Конфигурация модуля OCR анализа
import os

# Пути и настройки БД
DB_PATH = os.environ.get('DB_PATH', '/app/storage/database/analytics.db')
SCREENSHOTS_DIR = os.environ.get('SCREENSHOTS_DIR', '/app/storage/screenshots')

# Настройки Tesseract OCR
TESSERACT_LANG = os.environ.get('TESSERACT_LANG', 'rus+eng')

# OCR cache и метрики качества
OCR_CACHE_ENABLED = os.environ.get('OCR_CACHE_ENABLED', 'true').lower() in {'1', 'true', 'yes', 'y', 'on'}
OCR_CACHE_TTL_SECONDS = int(os.environ.get('OCR_CACHE_TTL_SECONDS', '86400'))
OCR_CACHE_MAX_ITEMS = int(os.environ.get('OCR_CACHE_MAX_ITEMS', '1000'))
OCR_CACHE_FILE = os.environ.get('OCR_CACHE_FILE', '/app/storage/ocr_cache.json')

# Параметры обработки
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '10'))
PROCESSING_INTERVAL = int(os.environ.get('PROCESSING_INTERVAL', '60'))

# Логирование
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
