"""
Модуль работы с базой данных (SQLite или PostgreSQL)
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Определение типа БД
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql').lower()

if DB_TYPE == 'postgresql':
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import sql
else:
    import sqlite3


class DatabaseManager:
    """Управление базой данных (SQLite или PostgreSQL)"""
    
    def __init__(self):
        """Инициализация подключения к БД"""
        self.db_type = DB_TYPE
        
        if self.db_type == 'postgresql':
            self.conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'postgres'),
                port=int(os.environ.get('DB_PORT', '5432')),
                database=os.environ.get('DB_NAME', 'screenshot_analytics'),
                user=os.environ.get('DB_USER', 'admin'),
                password=os.environ.get('DB_PASSWORD', 'changeme')
            )
            logger.info("Подключение к PostgreSQL установлено")
        else:
            db_path = os.environ.get('DB_PATH', '/app/storage/database/analytics.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Подключение к SQLite: {db_path}")
        
        self._create_tables()
    
    def _get_cursor(self):
        """Получение курсора в зависимости от типа БД"""
        if self.db_type == 'postgresql':
            return self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            return self.conn.cursor()
    
    def _create_tables(self):
        """Создание таблиц если они не существуют"""
        cursor = self._get_cursor()
        
        try:
            # Чтение SQL схемы из переменной окружения или файла
            init_sql_path = os.environ.get('INIT_SQL_PATH', '/docker-entrypoint-initdb.d/init.sql')
            
            if os.path.exists(init_sql_path):
                with open(init_sql_path, 'r', encoding='utf-8') as f:
                    sql_schema = f.read()
                cursor.execute(sql_schema)
                self.conn.commit()
                logger.info("Таблицы БД созданы/проверены")
            else:
                logger.warning("Файл init.sql не найден, таблицы не созданы")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    def register_employee(self, name: str) -> int:
        """
        Регистрирует сотрудника или возвращает существующий ID
        
        Args:
            name: Имя сотрудника
            
        Returns:
            ID сотрудника
        """
        cursor = self._get_cursor()
        
        # Проверка существования
        cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
        result = cursor.fetchone()
        
        if result:
            return result['id']
        
        # Создание нового сотрудника
        cursor.execute("INSERT INTO employees (name) VALUES (%s) RETURNING id", (name,))
        self.conn.commit()
        employee_id = cursor.fetchone()['id']
        
        logger.info(f"Зарегистрирован новый сотрудник: {name} (ID: {employee_id})")
        return employee_id
    
    def add_screenshot(self, employee_id: int, file_path: str, 
                      capture_date: str, capture_time: str) -> int:
        """
        Добавляет запись о скриншоте со статусом 'pending'
        
        Args:
            employee_id: ID сотрудника
            file_path: Путь к файлу скриншота
            capture_date: Дата снимка (YYYY-MM-DD)
            capture_time: Время снимка (HH:MM:SS)
            
        Returns:
            ID записи о скриншоте
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            INSERT INTO screenshots (employee_id, file_path, capture_date, capture_time, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id
        """, (employee_id, file_path, capture_date, capture_time))
        
        self.conn.commit()
        screenshot_id = cursor.fetchone()['id']
        
        logger.debug(f"Добавлен скриншот ID: {screenshot_id}")
        return screenshot_id
    
    def get_pending_screenshots(self, limit: int = 100) -> List[Dict]:
        """
        Возвращает список скриншотов для анализа
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            Список словарей с информацией о скриншотах
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT s.id, s.file_path, s.capture_date, s.capture_time, e.name as employee_name
            FROM screenshots s
            JOIN employees e ON s.employee_id = e.id
            WHERE s.status = 'pending'
            ORDER BY s.capture_date, s.capture_time
            LIMIT %s
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        logger.debug(f"Найдено {len(results)} скриншотов для анализа")
        
        return results
    
    def update_screenshot_status(self, screenshot_id: int, status: str):
        """
        Обновляет статус скриншота
        
        Args:
            screenshot_id: ID скриншота
            status: Новый статус ('pending', 'analyzed', 'error')
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            UPDATE screenshots SET status = %s WHERE id = %s
        """, (status, screenshot_id))
        
        self.conn.commit()
        logger.debug(f"Обновлен статус скриншота {screenshot_id}: {status}")
    
    def save_analysis_result(self, screenshot_id: int, ocr_text: str,
                            category: str, confidence: float):
        """
        Сохраняет результаты OCR анализа
        
        Args:
            screenshot_id: ID скриншота
            ocr_text: Распознанный текст
            category: Категория ('productive', 'unproductive', 'unknown')
            confidence: Уверенность классификации (0.0 - 1.0)
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            INSERT INTO analysis_results (screenshot_id, ocr_text, category, confidence)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (screenshot_id) DO UPDATE SET
                ocr_text = EXCLUDED.ocr_text,
                category = EXCLUDED.category,
                confidence = EXCLUDED.confidence,
                analyzed_at = CURRENT_TIMESTAMP
        """, (screenshot_id, ocr_text, category, confidence))
        
        self.conn.commit()
        logger.debug(f"Сохранен результат анализа для скриншота {screenshot_id}")
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")
    
    def __del__(self):
        """Деструктор"""
        self.close()
