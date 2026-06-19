"""
Классификатор ключевых слов
Определяет категорию скриншота на основе распознанного текста
Улучшен для определения открытых приложений и статуса работы
"""
import logging
import re
from typing import Tuple, Dict, List, Optional

logger = logging.getLogger(__name__)


class KeywordClassifier:
    """Классификатор по ключевым словам с определением приложений"""
    
    # Словари приложений для определения статуса
    WORK_APPLICATIONS = {
        'excel': ['excel', 'эксель', '.xlsx', '.xls'],
        'word': ['word', 'ворд', '.docx', '.doc'],
        'powerpoint': ['powerpoint', 'pptx', '.ppt'],
        'outlook': ['outlook', 'microsoft outlook'],
        '1c': ['1c', '1С'],
        'bitrix': ['bitrix', 'битрикс'],
        'figma': ['figma', 'фигма', '.fig'],
        'photoshop': ['photoshop', 'фотошоп', '.psd'],
        'vscode': ['vscode', 'visual studio code'],
        'jira': ['jira'],
        'slack': ['slack'],
        'teams': ['teams', 'microsoft teams'],
        'zoom': ['zoom'],
        'sap': ['sap', 'sap gui'],
        'browser_work': [
            'google docs', 'яндекс диск', 'dropbox', 'notion', 'trello', 'asana', 'confluence',
            'tinkoff', 'tinkoper', 'sberbank', 'сбербанк', 'whatsapp', 'web.whatsapp',
            'kontur', 'контур', 'экстерн', 'diadoc', 'диадок',
            'яндекс', 'yandex', 'google',
            'ифнс', 'налоговая', 'фнс',
            'инфо трейд', '1c инфо'
        ],
        'sql': ['postgresql', 'mysql', 'sqlite']
    }
    
    UNPRODUCTIVE_APPLICATIONS = {
        'youtube': ['youtube.com', 'youtube', 'youtu.be'],
        'vk': ['vk.com', 'vk.com/', 'vkontakte.ru', 'вконтакте.ру'],
        'ozon_wildberries': ['ozon', 'wildberries', 'wb.ru', 'маркетплейс'],
        'kinopoisk_ivi': ['kinopoisk', 'кинопоиск', 'ivi.ru', 'okko', 'more.tv'],
        'games': ['steam', 'epic games', 'twitch', 'wargaming', 'world of tanks', 'dota', 'cs:go'],
        'social': ['instagram', 'facebook', 'twitter', 'ok.ru', 'odnoklassniki', 'tiktok', 'reddit'],
        'shopping': ['aliexpress', 'alibaba', 'amazon']
    }
    
    def __init__(self, db):
        """
        Инициализация классификатора
        
        Args:
            db: Экземпляр DatabaseManager
        """
        self.db = db
        self.work_apps = self._flatten_dict(self.WORK_APPLICATIONS)
        self.unproductive_apps = self._flatten_dict(self.UNPRODUCTIVE_APPLICATIONS)
        logger.info("KeywordClassifier инициализирован с определением приложений")
    
    def _flatten_dict(self, app_dict: Dict) -> List[str]:
        """Преобразует словарь приложений в плоский список ключевых слов"""
        flat_list = []
        for keywords in app_dict.values():
            flat_list.extend(keywords)
        return flat_list
    
    def _clean_value(self, value: str, max_len: int = 40) -> str:
        """Очищает и обрезает значение детали от OCR-мусора"""
        # Заменяем множественные пробелы
        value = re.sub(r'\s+', ' ', value).strip()
        # Убираем текст после специальных символов (| < > [ ] { })
        value = re.split(r'[\|<>\[\]{}]', value)[0].strip()
        # Оставляем только буквы, цифры, точки, дефисы и русские символы
        value = re.sub(r'[^\w\s\.\-А-Яа-яЁё]', '', value).strip()
        # Не удаляем короткие слова - они могут быть значимыми ("и", "а", "но")
        value = re.sub(r'\s{2,}', ' ', value).strip()
        # Обрезаем до нужной длины
        if len(value) > max_len:
            value = value[:max_len].rsplit(' ', 1)[0]
        return value
    
    def _keyword_in_text(self, keyword: str, text_lower: str) -> bool:
        """Поиск ключевого слова с учетом OCR ошибок"""
        kw = keyword.lower()
        # Для очень коротких слов (1-2 символа) требуем строгие границы
        if len(kw) <= 2:
            return bool(re.search(rf'(?<![\w.]){re.escape(kw)}(?![\w.])', text_lower, re.IGNORECASE))
        # Для слов до 3 символов - границы слов
        if len(kw) <= 3:
            return bool(re.search(rf'\b{re.escape(kw)}\b', text_lower, re.IGNORECASE))
        
        # Для слов 4-6 символов тоже используем границы слова (чтобы избежать ложных срабатываний)
        if len(kw) <= 6:
            # Проверяем точное совпадение с границами ИЛИ начало слова
            # Например "bitrix" должен найти "bitrix24", но не "РИКС"
            if re.search(rf'\b{re.escape(kw)}', text_lower, re.IGNORECASE):
                return True
            # Также проверяем кириллический вариант
            if kw.isascii() and any(ord(c) > 127 for c in text_lower):
                # Если ключевое слово латиницей а текст содержит кириллицу,
                # проверяем транслитерацию или похожие написания
                pass
            return False
        
        # Для длинных слов (>6 символов) - сначала точное вхождение
        if kw in text_lower:
            return True
        
        # Если не нашли - проверяем частичное совпадение (для OCR ошибок)
        # Например "sberbank" может быть "sberbankrofmainzul"
        # Проверяем что хотя бы 80% символов ключевого слова есть в тексте последовательно
        min_match_len = max(5, int(len(kw) * 0.7))  # Минимум 70% или 5 символов
        for i in range(len(kw) - min_match_len + 1):
            substring = kw[i:i+min_match_len]
            if substring in text_lower:
                return True
        
        return False
    
    def extract_detailed_info(self, ocr_text: str) -> List[str]:
        """
        Извлекает детализированную информацию из текста
     
     
        
        Args:
            ocr_text: Распознанный текст
            
        Returns:
            Список коротких деталей (макс. 3 элемента)
        """
        text = ocr_text
        details = []
        
        # SAP транзакция (ME21N, VA01)
        sap_trans = re.search(
            r'(?:Транзакция|Transaction|T-code)[:\s]*([A-Z][A-Z0-9]{3,5})',
            text, re.IGNORECASE
        )
        if sap_trans:
            details.append(f"SAP: {sap_trans.group(1)}")
        
        # 1С — извлечение информации о базе
        if re.search(r'1[СC]', text, re.IGNORECASE):
            db_name = self._extract_1c_database(text)
            if db_name:
                details.append(f"1С база: {db_name}")
        
        # Excel / Word — только имя файла
        for pattern, label in [
            (r'([\w\-\.]+\.xlsx?)', 'Excel'),
            (r'([\w\-\.]+\.docx?)', 'Word'),
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filename = match.group(1)
                # Фильтруем системные файлы
                if not filename.startswith('~') and len(filename) > 5:
                    details.append(f"{label}: {filename}")
                break
        
        # SQL — извлечение имени таблицы или типа запроса
        # Проверяем наличие SQL контекста
        sql_keywords = ['select', 'insert', 'update', 'delete', 'from', 'where', 
                       'postgresql', 'mysql', 'sqlite', 'database', 'query']
        has_sql_context = any(kw in text.lower() for kw in sql_keywords)
        
        if has_sql_context:
            sql_detail = self._extract_sql_info(text)
            if sql_detail:
                details.append(sql_detail)
        
        return details[:3]  # Максимум 3 детали
    
    def _extract_1c_database(self, text: str) -> Optional[str]:
        """
        Извлекает название базы 1С из текста
        Приоритет: Пользователь > Конкретное название базы > Заголовок окна > Общие названия
        
        Args:
            text: OCR текст
            
        Returns:
            Название базы или None
        """
        # Паттерн 1: "Пользователь: Иванов А.А." или "Пользователь: Иванова Н.Н."
        user_match = re.search(
            r'Пользователь[:\s]+([А-ЯЁ][а-яё]+\s+[А-ЯЁA-Z]\.\s*[А-ЯЁA-Z]\.?)',
            text
        )
        if user_match:
            return self._clean_value(user_match.group(1), 30)
        
        # Паттерн 2: Конкретные названия баз в скобках или после двоеточия
        # Примеры: "ИНФО Трэйд (1С Предприятие)", "База: Торговый дом"
        specific_base_patterns = [
            # "ИНФО Трэйд (1С Предприятие)" или "Название (1С...)"
            r'([А-ЯЁ][А-ЯЁа-яё\s]{2,30})\s*\(\s*1[СC]',
            # "1С: ИНФО Трэйд" или "1С Предприятие: Название"
            r'1[СC][^:]*[:\-]\s*([А-ЯЁ][А-ЯЁа-яё\s]{3,40})(?:\s|$|\()',
            # "База данных: Название" или "Информационная база: Название"
            r'(?:База|Информационная база)[^:]*[:\-]\s*([А-ЯЁ][А-ЯЁа-яё\s]{3,40})',
        ]
        
        for pattern in specific_base_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                base_name = self._clean_value(match.group(1), 40)
                if base_name and len(base_name) > 3:
                    # Фильтруем общие слова и мусорные символы
                    base_name = re.sub(r'\b(Конфигуратор|Отладчик|Предприятие|Программа)\b', '', base_name, flags=re.IGNORECASE).strip()
                    # Проверяем что остались буквы (не просто мусор)
                    if base_name and re.search(r'[А-ЯЁа-яё]{3,}', base_name):
                        return base_name
        
        # Паттерн 3: Проверяем наличие имени с инициалами ДО общего паттерна 1С
        # Если есть имя с инициалами, сразу используем его
        fullname_match = re.search(
            r'([А-ЯЁ][а-яё]{2,}\s+[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.?)',
            text
        )
        if fullname_match:
            name = self._clean_value(fullname_match.group(1), 30)
            # Проверяем что это похоже на настоящее имя (не мусор)
            if name and re.search(r'[А-ЯЁ][а-яё]{2,}\s+[А-ЯЁA-Z]\.', name):
                return name
        
        # Паттерн 3: "1С: Предприятие" или "1С:Бухгалтерия"
        base_match = re.search(
            r'1[СC][:\s]*([А-ЯЁ][А-ЯЁа-яё\s]{3,40})',
            text,
            re.IGNORECASE
        )
        if base_match:
            base_name = self._clean_value(base_match.group(1), 35)
            # Фильтруем общие слова
            if base_name and len(base_name) > 3:
                # Убираем лишние слова вроде "Предприятие", "Конфигуратор"
                base_name = re.sub(r'\b(Конфигуратор|Отладчик|Предприятие)\b', '', base_name, flags=re.IGNORECASE).strip()
                # Проверяем что осталось что-то содержательное с буквами
                # НО: если похоже на имя с инициалами - пропускаем, пусть Паттерн 4 обработает
                if base_name and len(base_name) > 3 and re.search(r'[А-ЯЁа-яё]{3,}', base_name):
                    # Если содержит инициалы (буква.буква), лучше пропустить для Паттерна 4
                    if not re.search(r'[А-ЯЁA-Z]\.[А-ЯЁA-Z]', base_name):
                        return base_name
        
        # Паттерн 5: Общие названия баз 1С (более специфичные)
        common_bases = [
            r'\b(Бухгалтерия предприятия|Управление торговлей|Зарплата и кадры|Комплексная автоматизация)\b',
            r'\b(Розница|Производство\.Enterprise|Документооборот)\b'
        ]
        for pattern in common_bases:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Паттерн 6: Fallback - если есть "бухгалтерия" или "предприятие" без явного "1С"
        # Это помогает когда OCR плохо распознал "1С" как "1@" или другие символы
        text_lower = text.lower()
        if re.search(r'\bбухгалтерия\b', text_lower):
            # Проверяем есть ли контекст 1С (названия баз, документы)
            if any(word in text_lower for word in ['счет', 'реализация', 'накладная', 'покупатель', 'предприятие']):
                return 'Бухгалтерия'
        
        return None
    
    def _extract_sql_info(self, text: str) -> Optional[str]:
        """
        Извлекает информацию о SQL запросе
        
        Args:
            text: OCR текст
            
        Returns:
            Деталь SQL или None
        """
        # Тип запроса
        query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
        for qt in query_types:
            if re.search(rf'\b{qt}\b', text, re.IGNORECASE):
                return f"SQL: {qt}"
        
        # Имя таблицы
        table_match = re.search(
            r'(?:FROM|INTO|UPDATE|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            text, re.IGNORECASE
        )
        if table_match:
            return f"SQL таблица: {table_match.group(1)}"
        
        # PostgreSQL/MySQL
        if re.search(r'\bpostgresql\b', text, re.IGNORECASE):
            return "SQL: PostgreSQL"
        if re.search(r'\bmysql\b', text, re.IGNORECASE):
            return "SQL: MySQL"
        
        return None
    
    def _extract_browser_service(self, ocr_text: str) -> str:
        """
        Извлекает конкретный браузерный сервис из текста
        
        Args:
            ocr_text: Распознанный текст
            
        Returns:
            Название сервиса или пустая строка
        """
        text_lower = ocr_text.lower()
        
        # Список сервисов в порядке приоритета (более специфичные первыми)
        services = [
            ('diadoc', ['diadoc', 'диадок']),
            ('kontur', ['kontur', 'контур', 'экстерн']),
            ('sberbank', ['sberbank', 'сбербанк', 'sber']),
            ('tinkoff', ['tinkoff', 'tinkoper', 'тинькофф']),
            ('whatsapp', ['whatsapp', 'web.whatsapp']),
            ('yandex', ['яндекс', 'yandex']),
            ('google', ['google', 'googl']),  # "googl" для OCR ошибок типа "Googie"
            ('ifns', ['ифнс', 'налоговая', 'фнс']),
            ('info_trade', ['инфо трейд', '1c инфо']),
            ('notion', ['notion']),
            ('trello', ['trello']),
            ('asana', ['asana']),
            ('confluence', ['confluence']),
            ('dropbox', ['dropbox']),
        ]
        
        for service_name, keywords in services:
            for kw in keywords:
                if self._keyword_in_text(kw, text_lower):
                    # Возвращаем человекочитаемое название
                    service_names = {
                        'diadoc': 'Диадок',
                        'kontur': 'Контур',
                        'sberbank': 'Сбербанк',
                        'tinkoff': 'Тинькофф',
                        'whatsapp': 'WhatsApp',
                        'yandex': 'Яндекс',
                        'google': 'Google',
                        'ifns': 'ФНС',
                        'info_trade': 'Инфо Трейд',
                        'notion': 'Notion',
                        'trello': 'Trello',
                        'asana': 'Asana',
                        'confluence': 'Confluence',
                        'dropbox': 'Dropbox',
                    }
                    return service_names.get(service_name, service_name)
        
        return ''
    
    def build_details(self, ocr_text: str) -> str:
        """
        Формирует краткую строку деталей для отчёта.
        Пример: Рабочие: 1c; 1С база: Новикова Н. H
        """
        if not ocr_text or not ocr_text.strip():
            return 'Приложения не определены'
        
        text_lower = ocr_text.lower()
        parts = []
        
        work_apps = []
        for app_name, keywords in self.WORK_APPLICATIONS.items():
            if any(self._keyword_in_text(kw, text_lower) for kw in keywords):
                work_apps.append(app_name)
        
        # Дополнительная проверка для 1С через контекст
        if '1c' not in work_apps and re.search(r'1[СC]', ocr_text, re.IGNORECASE):
            # Если есть "1С" в тексте но не определилось как приложение
            # Проверяем есть ли специфичные детали
            db_name = self._extract_1c_database(ocr_text)
            if db_name:
                work_apps.insert(0, '1c')  # Добавляем 1С в начало
        
        personal_apps = []
        for app_name, keywords in self.UNPRODUCTIVE_APPLICATIONS.items():
            if any(self._keyword_in_text(kw, text_lower) for kw in keywords):
                personal_apps.append(app_name)
        
        extra = self.extract_detailed_info(ocr_text)
        
        if work_apps:
            # Если есть browser_work, заменяем его на конкретный сервис
            if 'browser_work' in work_apps:
                service = self._extract_browser_service(ocr_text)
                if service:
                    # Заменяем 'browser_work' на конкретный сервис
                    display_apps = [app if app != 'browser_work' else service for app in work_apps[:4]]
                    parts.append(f"Рабочие: {', '.join(display_apps)}")
                else:
                    parts.append(f"Рабочие: {', '.join(work_apps[:4])}")
            else:
                parts.append(f"Рабочие: {', '.join(work_apps[:4])}")
        elif personal_apps:
            parts.append(f"Личные: {', '.join(personal_apps[:3])}")
        
        parts.extend(extra)
        
        if not parts:
            return 'Приложения не определены'
        
        return '; '.join(parts)
    
    def detect_applications(self, ocr_text: str) -> Dict[str, any]:
        """
        Определяет открытые приложения по тексту
        и извлекает детализированную информацию
        
        Args:
            ocr_text: Распознанный текст
            
        Returns:
            Словарь с обнаруженными приложениями и деталями
        """
        text_lower = ocr_text.lower()
        
        detected = {
            'work_apps': [],
            'unproductive_apps': [],
            'details': ''
        }
        
        # Проверка рабочих приложений
        for app_name, keywords in self.WORK_APPLICATIONS.items():
            if any(self._keyword_in_text(kw, text_lower) for kw in keywords):
                detected['work_apps'].append(app_name)
        
        # Дополнительная проверка для 1С через контекст
        if '1c' not in detected['work_apps']:
            # Сначала проверяем явное "1С"
            has_1c_explicit = re.search(r'1[СC]', ocr_text, re.IGNORECASE)
            # Fallback: проверяем контекст 1С (бухгалтерия + документы)
            has_1c_context = (
                re.search(r'\bбухгалтерия\b', text_lower) and
                any(word in text_lower for word in ['счет', 'реализация', 'накладная', 'покупатель', 'предприятие'])
            )
            
            if has_1c_explicit or has_1c_context:
                db_name = self._extract_1c_database(ocr_text)
                if db_name:
                    detected['work_apps'].insert(0, '1c')
        
        # Проверка непродуктивных приложений
        for app_name, keywords in self.UNPRODUCTIVE_APPLICATIONS.items():
            if any(self._keyword_in_text(kw, text_lower) for kw in keywords):
                detected['unproductive_apps'].append(app_name)
        
        detected['details'] = self.build_details(ocr_text)
        
        return detected
    
    def classify(self, ocr_text: str) -> Tuple[str, float]:
        """
        Классифицирует текст по ключевым словам и приложениям
        
        Args:
            ocr_text: Распознанный текст из OCR
            
        Returns:
            Кортеж (category, confidence):
                - category: 'work', 'user', или 'unknown'
                - confidence: уверенность от 0.0 до 1.0
        """
        if not ocr_text or len(ocr_text.strip()) == 0:
            logger.debug("Пустой текст, категория: unknown")
            return ('unknown', 0.0)
        
        # Определение приложений
        app_detection = self.detect_applications(ocr_text)
        logger.debug(f"Обнаруженные приложения: {app_detection['details']}")
        
        # Если определены четкие приложения - используем их
        if app_detection['work_apps'] and not app_detection['unproductive_apps']:
            confidence = min(0.95, 0.7 + len(app_detection['work_apps']) * 0.1)
            logger.info(f"Категория: work (приложения: {app_detection['work_apps']}, confidence: {confidence:.2f})")
            return ('work', confidence)
        
        if app_detection['unproductive_apps'] and not app_detection['work_apps']:
            confidence = min(0.95, 0.7 + len(app_detection['unproductive_apps']) * 0.1)
            logger.info(f"Категория: user (приложения: {app_detection['unproductive_apps']}, confidence: {confidence:.2f})")
            return ('user', confidence)
        
        # Если есть и рабочие и личные - приоритет у рабочих
        if app_detection['work_apps'] and app_detection['unproductive_apps']:
            confidence = 0.6
            logger.info(f"Категория: work (смешано, приоритет рабочим)")
            return ('work', confidence)
        
        # Fallback: классическая классификация по ключевым словам из БД
        return self.classify_by_keywords(ocr_text)
    
    def classify_by_keywords(self, ocr_text: str) -> Tuple[str, float]:
        """
        Классическая классификация по ключевым словам из БД
        
        Args:
            ocr_text: Распознанный текст
            
        Returns:
            Кортеж (category, confidence)
        """
        text_lower = ocr_text.lower()
        
        # Загрузка словарей из БД
        try:
            productive_words = self.db.get_keywords('work')
            unproductive_words = self.db.get_keywords('user')
        except Exception as e:
            logger.warning(f"Ошибка загрузки слов из БД: {e}. Используем дефолтные категории.")
            return ('unknown', 0.0)
        
        # Подсчет совпадений
        prod_matches = [word for word in productive_words if word in text_lower]
        unprod_matches = [word for word in unproductive_words if word in text_lower]
        
        prod_count = len(prod_matches)
        unprod_count = len(unprod_matches)
        
        total = prod_count + unprod_count
        
        # Определение категории
        if total == 0:
            return ('unknown', 0.0)
        
        if prod_count > unprod_count:
            confidence = prod_count / total
            logger.info(f"Категория: work (по ключевым словам, confidence: {confidence:.2f})")
            return ('work', confidence)
        
        elif unprod_count > prod_count:
            confidence = unprod_count / total
            logger.info(f"Категория: user (по ключевым словам, confidence: {confidence:.2f})")
            return ('user', confidence)
        
        else:
            return ('unknown', 0.5)
