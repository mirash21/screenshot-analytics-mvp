"""
Модуль работы с базой данных для OCR анализатора (SQLite или PostgreSQL)
"""
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Определение типа БД
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql').lower()

if DB_TYPE == 'postgresql':
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3


class DatabaseManager:
    """Управление базой данных SQLite/PostgreSQL для модуля анализа"""
    
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
    
    def _get_cursor(self):
        """Получение курсора в зависимости от типа БД"""
        if self.db_type == 'postgresql':
            return self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            return self.conn.cursor()
    
    def get_pending_screenshots(self, limit: int = 10) -> List[Dict]:
        """
        Возвращает список скриншотов со статусом 'pending' для анализа
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            Список словарей с информацией о скриншотах
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT s.id, s.file_path, s.capture_date, s.capture_time, 
                   e.name as employee_name
            FROM screenshots s
            JOIN employees e ON s.employee_id = e.id
            WHERE s.status = 'pending'
            ORDER BY s.capture_date ASC, s.capture_time ASC
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
            status: Новый статус ('analyzed', 'error')
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            UPDATE screenshots SET status = %s WHERE id = %s
        """, (status, screenshot_id))
        
        self.conn.commit()
        logger.debug(f"Статус скриншота {screenshot_id} обновлен: {status}")
    
    def save_analysis_result(self, screenshot_id: int, ocr_text: str,
                            category: str, confidence: float, details: str = ''):
        """
        Сохраняет результаты OCR анализа
        
        Args:
            screenshot_id: ID скриншота
            ocr_text: Распознанный текст
            category: Категория ('work', 'user', 'unknown')
            confidence: Уверенность классификации (0.0 - 1.0)
            details: Детали (обнаруженные приложения)
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            INSERT INTO analysis_results (screenshot_id, ocr_text, category, confidence, details, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (screenshot_id) DO UPDATE SET
                ocr_text = EXCLUDED.ocr_text,
                category = EXCLUDED.category,
                confidence = EXCLUDED.confidence,
                details = EXCLUDED.details,
                analyzed_at = CURRENT_TIMESTAMP
        """, (screenshot_id, ocr_text, category, confidence, details))
        
        self.conn.commit()
        logger.debug(f"Результат анализа сохранен для скриншота {screenshot_id}")
    
    def get_keywords(self, category: str) -> List[str]:
        """
        Получает список ключевых слов указанной категории
        
        Args:
            category: Категория ('work', 'user', или legacy 'productive'/'unproductive')
            
        Returns:
            Список ключевых слов
        """
        cursor = self._get_cursor()
        
        if category == 'productive':
            category = 'work'
        elif category == 'unproductive':
            category = 'user'
        
        cursor.execute("""
            SELECT word FROM keywords WHERE category = %s
        """, (category,))
        
        results = [row['word'] for row in cursor.fetchall()]
        logger.debug(f"Загружено {len(results)} ключевых слов категории '{category}'")
        
        return results
    
    def add_keyword(self, word: str, category: str, created_by: str = 'admin'):
        """
        Добавляет новое ключевое слово
        
        Args:
            word: Ключевое слово
            category: Категория ('work' или 'user')
            created_by: Кто добавил ('system' или 'admin')
        """
        cursor = self._get_cursor()
        
        if category == 'productive':
            category = 'work'
        elif category == 'unproductive':
            category = 'user'
        
        try:
            cursor.execute("""
                INSERT INTO keywords (word, category, created_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (word) DO NOTHING
            """, (word.lower(), category, created_by))
            
            self.conn.commit()
            logger.info(f"Добавлено ключевое слово: {word} ({category})")
        
        except Exception as e:
            logger.warning(f"Ошибка добавления ключевого слова {word}: {e}")
    
    def delete_keyword(self, word: str):
        """
        Удаляет ключевое слово
        
        Args:
            word: Ключевое слово для удаления
        """
        cursor = self._get_cursor()
        
        cursor.execute("DELETE FROM keywords WHERE word = %s", (word.lower(),))
        self.conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Удалено ключевое слово: {word}")
        else:
            logger.warning(f"Ключевое слово не найдено: {word}")
    
    def load_default_keywords(self):
        """Загружает стандартные ключевые слова"""
        work_keywords = [
            '1с', '1c', 'битрикс', 'bitrix', 'excel', 'word', 'powerpoint',
            'crm', 'почта', 'mail', 'outlook', 'figma', 'photoshop',
            'jira', 'confluence', 'slack', 'teams', 'zoom', 'skype',
            'sap', 'oracle', 'sql', 'python', 'java', 'javascript',
            'github', 'gitlab', 'visual studio', 'vscode', 'google docs',
            'яндекс диск', 'dropbox', 'notion', 'trello', 'asana',
            'документ', 'отчет', 'задача', 'сделка', 'лид', 'счета',
            'накладная', 'бухгалтерия', 'презентация', 'макет', 'прототип'
        ]
        
        user_keywords = [
            'youtube.com', 'youtube', 'vk.com', 'vk', 'vkontakte',
            'wildberries', 'wb.ru', 'ozon', 'ozon.ru', 'кинопоиск',
            'kinopoisk', 'steam', 'epic games', 'twitch', 'tiktok',
            'instagram', 'facebook', 'twitter', 'ok.ru', 'odnoklassniki',
            'reddit', 'netflix', 'ivi', 'okko', 'more.tv', 'wargaming',
            'world of tanks', 'дота', 'dota', 'cs:go', 'counter-strike',
            'фильм', 'сериал', 'музыка', 'видео', 'магазин', 'купить'
        ]
        
        for word in work_keywords:
            try:
                self.add_keyword(word, 'work', 'system')
            except Exception:
                pass
        
        for word in user_keywords:
            try:
                self.add_keyword(word, 'user', 'system')
            except Exception:
                pass
        
        logger.info(f"Загружено {len(work_keywords) + len(user_keywords)} стандартных ключевых слов")
    
    # Методы для дашборда
    def get_productivity_stats(self, date_from: str, date_to: str) -> Dict:
        """
        Получает общую статистику продуктивности
        
        Args:
            date_from: Начальная дата (YYYY-MM-DD)
            date_to: Конечная дата (YYYY-MM-DD)
            
        Returns:
            Словарь со статистикой
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(s.id) as total_screenshots,
                SUM(CASE WHEN ar.category IN ('work', 'productive') THEN 1 ELSE 0 END) as productive_count,
                SUM(CASE WHEN ar.category IN ('user', 'unproductive') THEN 1 ELSE 0 END) as unproductive_count,
                SUM(CASE WHEN ar.category = 'unknown' OR ar.category IS NULL THEN 1 ELSE 0 END) as unknown_count
            FROM screenshots s
            LEFT JOIN analysis_results ar ON s.id = ar.screenshot_id
            WHERE s.capture_date BETWEEN %s AND %s
            AND s.status = 'analyzed'
        """, (date_from, date_to))
        
        result = dict(cursor.fetchone())
        return result
    
    def get_daily_productivity(self, date_from: str, date_to: str) -> List[Dict]:
        """
        Получает данные продуктивности по дням
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            Список словарей с данными по дням
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT 
                s.capture_date as date,
                COUNT(s.id) as total,
                SUM(CASE WHEN ar.category IN ('work', 'productive') THEN 1 ELSE 0 END) as productive,
                ROUND(
                    CAST(SUM(CASE WHEN ar.category IN ('work', 'productive') THEN 1 ELSE 0 END) AS NUMERIC) * 100 / 
                    NULLIF(COUNT(s.id), 0), 
                    2
                ) as productivity_percentage
            FROM screenshots s
            LEFT JOIN analysis_results ar ON s.id = ar.screenshot_id
            WHERE s.capture_date BETWEEN %s AND %s
            AND s.status = 'analyzed'
            GROUP BY s.capture_date
            ORDER BY s.capture_date
        """, (date_from, date_to))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_employee_ranking(self, date_from: str, date_to: str) -> List[Dict]:
        """
        Получает рейтинг сотрудников по продуктивности
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            Список сотрудников с метриками продуктивности
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT 
                e.name,
                COUNT(s.id) as total_screenshots,
                SUM(CASE WHEN ar.category IN ('work', 'productive') THEN 1 ELSE 0 END) as productive_count,
                ROUND(
                    CAST(SUM(CASE WHEN ar.category IN ('work', 'productive') THEN 1 ELSE 0 END) AS NUMERIC) * 100 / 
                    NULLIF(COUNT(s.id), 0), 
                    2
                ) as productive_pct
            FROM employees e
            JOIN screenshots s ON e.id = s.employee_id
            LEFT JOIN analysis_results ar ON s.id = ar.screenshot_id
            WHERE s.capture_date BETWEEN %s AND %s
            AND s.status = 'analyzed'
            GROUP BY e.id, e.name
            ORDER BY productive_pct DESC
        """, (date_from, date_to))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_employees(self) -> List[Dict]:
        """Получает список всех сотрудников"""
        cursor = self._get_cursor()
        cursor.execute("SELECT id, name FROM employees ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_employee_id(self, name: str) -> Optional[int]:
        """Получает ID сотрудника по имени"""
        cursor = self._get_cursor()
        cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def get_employee_screenshots(self, employee_id: int, date: str) -> List[Dict]:
        """
        Получает все скриншоты сотрудника за указанную дату
        
        Args:
            employee_id: ID сотрудника
            date: Дата (YYYY-MM-DD)
            
        Returns:
            Список скриншотов с результатами анализа
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT 
                s.id,
                s.file_path,
                s.capture_time,
                s.capture_date,
                ar.category,
                ar.confidence,
                ar.ocr_text,
                ar.details
            FROM screenshots s
            LEFT JOIN analysis_results ar ON s.id = ar.screenshot_id
            WHERE s.employee_id = %s
            AND s.capture_date = %s
            AND s.status = 'analyzed'
            ORDER BY s.capture_time
        """, (employee_id, date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_unproductive_screenshots(self, date_from: str, date_to: str) -> List[Dict]:
        """
        Получает все непродуктивные скриншоты за период
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            Список непродуктивных скриншотов
        """
        cursor = self._get_cursor()
        
        cursor.execute("""
            SELECT 
                s.id,
                s.file_path,
                s.capture_date,
                s.capture_time,
                e.name as employee_name,
                ar.ocr_text,
                ar.confidence,
                ar.details
            FROM screenshots s
            JOIN employees e ON s.employee_id = e.id
            JOIN analysis_results ar ON s.id = ar.screenshot_id
            WHERE s.capture_date BETWEEN %s AND %s
            AND ar.category IN ('user', 'unproductive')
            AND s.status = 'analyzed'
            ORDER BY s.capture_date DESC, s.capture_time DESC
        """, (date_from, date_to))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с БД закрыто")
    
    def __del__(self):
        """Деструктор"""
        self.close()
