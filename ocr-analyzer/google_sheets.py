"""
Модуль интеграции с Google Sheets
Отправляет данные о статусе работы сотрудников в Google Таблицы
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Google API библиотеки не установлены. Google Sheets интеграция недоступна.")


logger = logging.getLogger(__name__)


class GoogleSheetsIntegration:
    """Интеграция с Google Sheets API"""
    
    def __init__(self):
        """
        Инициализация подключения к Google Sheets
        
        Args:
            service_account_file: Путь к JSON ключу Service Account
            spreadsheet_id: ID Google Таблицы
            sheet_name: Название листа (по умолчанию 'Лист1')
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google API библиотеки не установлены. Установите: google-auth google-auth-oauthlib google-api-python-client")
        
        self.service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', '')
        self.spreadsheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID', '')
        self.sheet_name = os.environ.get('GOOGLE_SHEET_NAME', 'Лист1')
        
        if not self.service_account_file or not self.spreadsheet_id:
            logger.warning("Google Sheets не настроен: отсутствует Service Account или ID таблицы")
            self.service = None
            return
        
        try:
            # Написание OAuth2 credentials
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=scopes
            )
            
            # Создание API клиента
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info(f"Google Sheets интеграция инициализирована: {self.spreadsheet_id}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Google Sheets: {e}")
            self.service = None
    
    def _ensure_header_exists(self):
        """Проверка и создание заголовков если лист пустой"""
        if not self.service:
            return False
        
        try:
            # Проверка наличия данных
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:E1"
            ).execute()
            
            values = result.get('values', [])
            
            # Если лист пустой, создаем заголовки
            if not values or len(values) == 0:
                headers = [['Дата', 'Время', 'Сотрудник', 'Статус', 'Детали']]
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1",
                    valueInputOption='USER_ENTERED',
                    body={'values': headers}
                ).execute()
                logger.info("Созданы заголовки в Google Sheets")
            
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка проверки заголовков: {e}")
            return False
    
    def send_record(self, employee_name: str, capture_date: str, capture_time: str,
                   status: str, details: str):
        """
        Отправляет одну запись в Google Sheets
        
        Args:
            employee_name: Имя сотрудника
            capture_date: Дата (YYYY-MM-DD)
            capture_time: Время (HH:MM:SS)
            status: Статус ('work', 'user', 'unknown')
            details: Детали (обнаруженные приложения)
        """
        if not self.service:
            logger.warning("Google Sheets не настроен. Запись не отправлена.")
            return False
        
        try:
            # Форматирование статуса для отображения
            status_display = 'Работа' if status == 'work' else ('Личное' if status == 'user' else 'Неизвестно')
            
            # Форматирование времени (убираем секунды если есть)
            time_display = capture_time[:5] if len(capture_time) >= 5 else capture_time
            
            # Данные для записи
            values = [[capture_date, time_display, employee_name, status_display, details]]
            
            # Добавление строки
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"Запись отправлена в Google Sheets: {employee_name} | {capture_date} {time_display} | {status_display}")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка отправки записи в Google Sheets: {e}")
            return False
    
    def send_batch_records(self, records: List[Dict]):
        """
        Отправляет пакет записей в Google Sheets
        
        Args:
            records: Список словарей с данными
                {employee_name, capture_date, capture_time, status, details}
        """
        if not self.service or not records:
            return False
        
        try:
            # Форматирование записей
            values = []
            for record in records:
                status_display = 'Работа' if record['status'] == 'work' else (
                    'Личное' if record['status'] == 'user' else 'Неизвестно'
                )
                time_display = record['capture_time'][:5] if len(record['capture_time']) >= 5 else record['capture_time']
                
                values.append([
                    record['capture_date'],
                    time_display,
                    record['employee_name'],
                    status_display,
                    record.get('details', '')
                ])
            
            # Пакетная отправка
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"Пакет из {len(values)} записей отправлен в Google Sheets")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка отправки пакета в Google Sheets: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Тестирует подключение к Google Sheets
        
        Returns:
            True если подключение успешно
        """
        if not self.service:
            return False
        
        try:
            # Простой запрос для проверки подключения
            self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            logger.info("Тест подключения к Google Sheets успешен")
            return True
        except HttpError as e:
            logger.error(f"Ошибка теста подключения: {e}")
            return False
