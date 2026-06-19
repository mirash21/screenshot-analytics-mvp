#!/usr/bin/env python3
"""
Скрипт для отправки существующих результатов анализа в Google Sheets
"""

import os
import sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Настройки из окружения
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'screenshot_analytics')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')

GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/app/config/service_account.json')
GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', '')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Лист1')

try:
    import psycopg2
except ImportError:
    print("Установите psycopg2: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_pending_results(limit=100):
    """Получить результаты которые еще не отправлены в Google Sheets"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем результаты анализа с информацией о сотруднике
    cursor.execute("""
        SELECT 
            ar.id,
            s.id as screenshot_id,
            e.name as employee_name,
            s.capture_date,
            s.capture_time,
            ar.category,
            ar.confidence,
            ar.analyzed_at
        FROM analysis_results ar
        JOIN screenshots s ON ar.screenshot_id = s.id
        JOIN employees e ON s.employee_id = e.id
        WHERE ar.google_synced = FALSE OR ar.google_synced IS NULL
        ORDER BY s.capture_date DESC, s.capture_time DESC
        LIMIT %s
    """, (limit,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return results


def send_to_google_sheets(records):
    """Отправить записи в Google Sheets"""
    if not GOOGLE_SPREADSHEET_ID:
        print("⚠️  GOOGLE_SPREADSHEET_ID не установлен в .env")
        return False
    
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        print(f"⚠️  Service Account файл не найден: {GOOGLE_SERVICE_ACCOUNT_FILE}")
        return False
    
    try:
        # Аутентификация
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        
        # Форматирование данных
        values = []
        for record in records:
            ar_id, screenshot_id, employee_name, capture_date, capture_time, category, confidence, analyzed_at = record
            
            # Форматируем детали
            details = f"Категория: {category}, Уверенность: {confidence:.2f}"
            
            values.append([
                capture_date.strftime('%Y-%m-%d') if capture_date else '',
                capture_time.strftime('%H:%M:%S') if capture_time else '',
                employee_name or 'Unknown',
                category,
                details
            ])
        
        if not values:
            print("Нет записей для отправки")
            return True
        
        # Отправка данных
        body = {'values': values}
        range_name = f'{GOOGLE_SHEET_NAME}!A:E'
        
        result = sheet.values().append(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"✅ Отправлено {len(values)} записей в Google Sheets")
        print(f"   Вставлено строк: {result.get('updates', {}).get('updatedRows', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки в Google Sheets: {e}")
        return False


def mark_as_synced(result_ids):
    """Пометить результаты как отправленные"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for result_id in result_ids:
        try:
            cursor.execute("""
                UPDATE analysis_results 
                SET google_synced = TRUE, google_synced_at = NOW()
                WHERE id = %s
            """, (result_id,))
        except Exception as e:
            print(f"Ошибка обновления статуса для ID {result_id}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()


def main():
    print("=" * 60)
    print("Синхронизация результатов анализа с Google Sheets")
    print("=" * 60)
    
    if not GOOGLE_SPREADSHEET_ID:
        print("\n⚠️  Google Sheets не настроен:")
        print("   Установите GOOGLE_SPREADSHEET_ID в файле .env")
        print("\nПример:")
        print("   GOOGLE_SPREADSHEET_ID=ваш_id_таблицы")
        return
    
    print(f"\n📊 Spreadsheet ID: {GOOGLE_SPREADSHEET_ID}")
    print(f"📝 Лист: {GOOGLE_SHEET_NAME}")
    
    # Получаем результаты
    print("\n📥 Получение результатов анализа...")
    results = get_pending_results(limit=100)
    
    if not results:
        print("✅ Все результаты уже отправлены в Google Sheets")
        return
    
    print(f"📋 Найдено {len(results)} записей для отправки")
    
    # Отправляем в Google Sheets
    print("\n📤 Отправка в Google Sheets...")
    success = send_to_google_sheets(results)
    
    if success:
        # Помечаем как отправленные
        result_ids = [r[0] for r in results]
        mark_as_synced(result_ids)
        print("✅ Результаты помечены как отправленные")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
