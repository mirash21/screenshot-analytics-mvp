"""
Главный скрипт модуля OCR анализа
Обрабатывает скриншоты со статусом 'pending' и классифицирует их
Отправляет данные в Google Sheets
"""
import os
import sys
import time
import logging

# Добавление пути для импорта модулей
sys.path.insert(0, '/app')

from config import DB_PATH, SCREENSHOTS_DIR, TESSERACT_LANG, BATCH_SIZE, PROCESSING_INTERVAL, LOG_LEVEL
from database import DatabaseManager
from ocr_engine import OCREngine
from keyword_classifier import KeywordClassifier
from google_sheets import GoogleSheetsIntegration

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/storage/analyzer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Основной цикл анализа скриншотов"""
    logger.info("=" * 60)
    logger.info("Запуск модуля OCR анализа")
    logger.info(f"База данных: {DB_PATH}")
    logger.info(f"Директория скриншотов: {SCREENSHOTS_DIR}")
    logger.info(f"Языки OCR: {TESSERACT_LANG}")
    logger.info(f"Размер батча: {BATCH_SIZE}")
    logger.info(f"Интервал проверки: {PROCESSING_INTERVAL} сек")
    logger.info("=" * 60)
    
    # Инициализация компонентов
    db = DatabaseManager()
    ocr = OCREngine(lang=TESSERACT_LANG)
    classifier = KeywordClassifier(db)
    
    # Инициализация Google Sheets интеграции
    try:
        google_sheets = GoogleSheetsIntegration()
        if google_sheets.service:
            logger.info("Google Sheets интеграция готова к работе")
            # Проверка и создание заголовков
            google_sheets._ensure_header_exists()
    except Exception as e:
        logger.warning(f"Google Sheets не инициализирован: {e}")
        google_sheets = None
    
    # Загрузка начальных ключевых слов если база пустая
    try:
        existing_keywords = db.get_keywords('work') + db.get_keywords('user')
        if len(existing_keywords) == 0:
            logger.info("База ключевых слов пуста, загрузка стандартных слов...")
            db.load_default_keywords()
    except Exception as e:
        logger.error(f"Ошибка загрузки ключевых слов: {e}")
        try:
            db.conn.rollback()
        except:
            pass
    
    processed_count = 0
    error_count = 0
    
    try:
        while True:
            logger.info("\n" + "=" * 60)
            logger.info(f"Начало цикла анализа (обработано: {processed_count}, ошибок: {error_count})")
            
            try:
                # Получение скриншотов со статусом 'pending'
                pending = db.get_pending_screenshots(limit=BATCH_SIZE)
                
                if not pending:
                    logger.info("Нет скриншотов для анализа")
                    time.sleep(PROCESSING_INTERVAL)
                    continue
                
                logger.info(f"Найдено {len(pending)} скриншотов для обработки")
                
                # Список для пакетной отправки в Google Sheets
                google_records = []
                
                # Обработка каждого скриншота
                for screenshot in pending:
                    try:
                        screenshot_id = screenshot['id']
                        file_path = screenshot['file_path']
                        employee_name = screenshot['employee_name']
                        capture_date = screenshot['capture_date']
                        capture_time = screenshot['capture_time']
                        
                        logger.info(f"\nОбработка скриншота ID={screenshot_id} "
                                  f"({employee_name})")
                        
                        # Проверка существования файла
                        if not os.path.exists(file_path):
                            logger.warning(f"Файл не найден: {file_path}")
                            db.update_screenshot_status(screenshot_id, 'error')
                            error_count += 1
                            continue
                        
                        # Шаг 1: OCR распознавание
                        logger.debug("Запуск OCR...")
                        ocr_result = ocr.extract_text_with_metrics(file_path)
                        ocr_text = ocr_result.text
                        logger.debug(
                            f"OCR завершен, длина текста: {len(ocr_text)}, "
                            f"движок: {ocr_result.engine}, confidence: {ocr_result.confidence:.2f}, "
                            f"duration_ms: {ocr_result.duration_ms:.1f}"
                        )

                        # Шаг 2: Классификация (определение приложений)
                        logger.debug("Запуск классификации...")
                        category, confidence = classifier.classify(ocr_text)

                        app_details = classifier.build_details(ocr_text)

                        logger.info(f"Классификация: {category} ({confidence:.2f}) | {app_details[:80]}")

                        # Шаг 3: Сохранение результатов в БД
                        db.save_analysis_result(
                            screenshot_id=screenshot_id,
                            ocr_text=ocr_text,
                            category=category,
                            confidence=confidence,
                            details=app_details,
                            ocr_engine=ocr_result.engine,
                            ocr_duration_ms=int(ocr_result.duration_ms),
                            ocr_metrics=ocr_result.metrics_dict()
                        )
                        
                        # Шаг 4: Обновление статуса скриншота
                        db.update_screenshot_status(screenshot_id, 'analyzed')
                        
                        # Шаг 5: Подготовка записи для Google Sheets
                        if google_sheets and google_sheets.service:
                            google_records.append({
                                'employee_name': employee_name,
                                'capture_date': str(capture_date),
                                'capture_time': str(capture_time),
                                'status': category,
                                'details': app_details
                            })
                        
                        processed_count += 1
                        logger.info(f"✓ Скриншот {screenshot_id} обработан: "
                                  f"{category} (уверенность: {confidence:.2f})")
                    
                    except Exception as e:
                        logger.error(f"Ошибка обработки скриншота {screenshot.get('id', 'unknown')}: {e}", 
                                   exc_info=True)
                        try:
                            db.update_screenshot_status(screenshot['id'], 'error')
                        except:
                            pass
                        error_count += 1
                
                # Пакетная отправка в Google Sheets
                if google_sheets and google_sheets.service and google_records:
                    logger.info(f"Отправка {len(google_records)} записей в Google Sheets...")
                    google_sheets.send_batch_records(google_records)
                
                logger.info(f"\nБатч завершен. Обработано: {processed_count}, "
                          f"Ошибок: {error_count}")
            
            except Exception as e:
                logger.error(f"Ошибка в цикле анализа: {e}", exc_info=True)
                time.sleep(PROCESSING_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\nПолучен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("Модуль OCR анализа остановлен")


if __name__ == "__main__":
    main()
