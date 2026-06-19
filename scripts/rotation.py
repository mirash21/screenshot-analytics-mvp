"""
Скрипт автоматической очистки старых скриншотов
Запускается раз в день для удаления файлов старше 30 дней
"""
import os
import sys
from datetime import datetime, timedelta

# Определение типа БД
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql').lower()

if DB_TYPE == 'postgresql':
    import psycopg2
else:
    import sqlite3

DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_NAME = os.environ.get('DB_NAME', 'screenshot_analytics')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'changeme')
DB_PATH = os.environ.get('DB_PATH', '/app/storage/database/analytics.db')

SCREENSHOTS_DIR = os.environ.get('SCREENSHOTS_DIR', '/app/storage/screenshots')
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))


def cleanup_old_screenshots():
    """Удаляет скриншоты и записи БД старше указанного периода"""
    print(f"Начало очистки данных старше {RETENTION_DAYS} дней...")
    
    # Подключение к БД
    if DB_TYPE == 'postgresql':
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    else:
        conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime('%Y-%m-%d')
    
    # Получение списка старых скриншотов
    cursor.execute("""
        SELECT id, file_path FROM screenshots
        WHERE capture_date < %s
    """, (cutoff_date,))
    
    old_screenshots = cursor.fetchall()
    
    deleted_files = 0
    deleted_records = 0
    
    for screenshot_id, file_path in old_screenshots:
        try:
            # Удаление файла
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files += 1
            
            # Удаление записи из analysis_results
            cursor.execute("DELETE FROM analysis_results WHERE screenshot_id = %s", (screenshot_id,))
            
            # Удаление записи из screenshots
            cursor.execute("DELETE FROM screenshots WHERE id = %s", (screenshot_id,))
            deleted_records += 1
        
        except Exception as e:
            print(f"Ошибка удаления {file_path}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Удалено файлов: {deleted_files}")
    print(f"✓ Удалено записей из БД: {deleted_records}")
    
    # Очистка пустых папок
    cleanup_empty_directories()


def cleanup_empty_directories():
    """Удаляет пустые директории в хранилище"""
    print("\nОчистка пустых директорий...")
    
    removed_count = 0
    for root, dirs, files in os.walk(SCREENSHOTS_DIR, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed_count += 1
                    print(f"  Удалена пустая папка: {dir_path}")
            except Exception as e:
                print(f"  Ошибка удаления папки {dir_path}: {e}")
    
    print(f"✓ Удалено пустых папок: {removed_count}")


if __name__ == "__main__":
    try:
        cleanup_old_screenshots()
        print("\n✅ Очистка завершена успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)
