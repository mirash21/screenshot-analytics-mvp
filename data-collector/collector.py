"""
Главный скрипт модуля сбора данных
Сканирует входящую папку, парсит метаданные и переносит файлы в хранилище
"""
import os
import sys
import time
import shutil
import logging
from pathlib import Path

# Добавление пути для импорта модулей
sys.path.insert(0, '/app')

from config import UPLOAD_DIR, SCREENSHOTS_DIR, DB_PATH, SCAN_INTERVAL_SECONDS, LOG_LEVEL
from file_parser import parse_screenshot_path, validate_screenshot_format
from database import DatabaseManager

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/storage/collector.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def scan_directory(directory: str) -> list:
    """
    Сканирует директорию на наличие новых файлов изображений
    
    Args:
        directory: Путь к директории для сканирования
        
    Returns:
        Список путей к найденным файлам
    """
    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
    files = []
    
    if not os.path.exists(directory):
        logger.warning(f"Директория не существует: {directory}")
        return files
    
    # Рекурсивный обход директории
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            
            # Проверка расширения
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                files.append(file_path)
    
    logger.info(f"Найдено {len(files)} файлов в {directory}")
    return files


def process_screenshot(file_path: str, db: DatabaseManager) -> bool:
    """
    Обрабатывает один скриншот: парсит метаданные, копирует файл, записывает в БД
    
    Args:
        file_path: Путь к файлу скриншота
        db: Экземпляр DatabaseManager
        
    Returns:
        True если обработка успешна, False иначе
    """
    try:
        # Валидация формата пути
        if not validate_screenshot_format(file_path):
            logger.warning(f"Неверный формат пути, пропуск: {file_path}")
            return False
        
        # Парсинг метаданных
        metadata = parse_screenshot_path(file_path)
        logger.info(f"Обработка: {metadata['employee_name']} / {metadata['date']} / {metadata['time']}")
        
        # Регистрация сотрудника
        employee_id = db.register_employee(metadata['employee_name'])
        
        # Формирование целевого пути
        # Структура: SCREENSHOTS_DIR/YYYY-MM-DD/EmployeeName/filename
        target_dir = os.path.join(
            SCREENSHOTS_DIR,
            metadata['date'],
            metadata['employee_name']
        )
        os.makedirs(target_dir, exist_ok=True)
        
        target_path = os.path.join(target_dir, metadata['filename'])
        
        # Проверка существования файла (избегаем дубликатов)
        if os.path.exists(target_path):
            logger.warning(f"Файл уже существует, пропуск: {target_path}")
            return False
        
        # Копирование файла с сохранением метаданных
        shutil.copy2(file_path, target_path)
        logger.debug(f"Файл скопирован: {target_path}")
        
        # Запись в базу данных
        screenshot_id = db.add_screenshot(
            employee_id=employee_id,
            file_path=target_path,
            capture_date=metadata['date'],
            capture_time=metadata['time']
        )
        logger.info(f"Запись в БД создана: ID={screenshot_id}")
        
        # Удаление исходного файла
        os.remove(file_path)
        logger.info(f"Исходный файл удален: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка обработки файла {file_path}: {e}", exc_info=True)
        return False


def main():
    """Основной цикл сбора данных"""
    logger.info("=" * 60)
    logger.info("Запуск модуля сбора данных")
    logger.info(f"Входящая директория: {UPLOAD_DIR}")
    logger.info(f"Целевая директория: {SCREENSHOTS_DIR}")
    logger.info(f"База данных: {DB_PATH}")
    logger.info(f"Интервал сканирования: {SCAN_INTERVAL_SECONDS} сек")
    logger.info("=" * 60)
    
    # Инициализация БД
    db = DatabaseManager()
    
    processed_count = 0
    error_count = 0
    
    try:
        while True:
            logger.info("\n" + "=" * 60)
            logger.info(f"Начало цикла сканирования (обработано: {processed_count}, ошибок: {error_count})")
            
            # Сканирование директории
            new_files = scan_directory(UPLOAD_DIR)
            
            if not new_files:
                logger.info("Новых файлов не найдено")
            else:
                logger.info(f"Обработка {len(new_files)} файлов...")
                
                # Обработка каждого файла
                for file_path in new_files:
                    success = process_screenshot(file_path, db)
                    
                    if success:
                        processed_count += 1
                    else:
                        error_count += 1
            
            logger.info(f"Цикл завершен. Ожидание {SCAN_INTERVAL_SECONDS} секунд...")
            time.sleep(SCAN_INTERVAL_SECONDS)
    
    except KeyboardInterrupt:
        logger.info("\nПолучен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("Модуль сбора данных остановлен")


if __name__ == "__main__":
    main()
