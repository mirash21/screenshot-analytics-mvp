"""
Тест улучшения извлечения деталей для 1С и SQL
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    """Mock database для тестирования"""
    def get_keywords(self, category):
        return []


def test_1c_extraction():
    """Тест извлечения информации о базах 1С"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст, ожидаемый результат)
        # Паттерн 1: Пользователь
        ("1С: Предприятие Пользователь: Иванова Н.Н.", "1С база: Иванова Н.Н."),
        ("Пользователь: Петров А.А. 1С Бухгалтерия", "1С база: Петров А.А."),
        
        # Паттерн 2: Название компании в скобках
        ("ИНФО Трэйд (1С Предприятие)", "1С база: ИНФО Трэйд"),
        ("Торговый Дом (1С:Управление торговлей)", "1С база: Торговый Дом"),
        ("Компания Альфа (1С Бухгалтерия)", "1С база: Компания Альфа"),
        
        # Паттерн 3: Конкретные названия баз
        ("1С:Бухгалтерия предприятия", "1С база:"),  # Должно найти "Бухгалтерия предприятия"
        ("Конфигуратор 1С: Управление торговлей", "1С база: Управление торговлей"),
        ("1С Зарплата и кадры", "1С база: Зарплата и кадры"),
        
        # Паттерн 4: Имя в контексте
        ("1С Предприятие Сидоров М.В.", "1С база: Сидоров М.В."),
        
        # Фильтрация мусора и общих слов
        ("1С: Предприятие", None),  # Только общее слово - должно фильтроваться
        ("Простой текст без 1С", None),
        ("1С: Конфигуратор", None),  # Только системное слово
    ]
    
    print("="*60)
    print("ТЕСТ ИЗВЛЕЧЕНИЯ ИНФОРМАЦИИ 1С")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for i, (text, expected_prefix) in enumerate(test_cases, 1):
        details = classifier.extract_detailed_info(text)
        result = details[0] if details else None
        
        # Проверка результата
        if expected_prefix is None:
            success = result is None
        else:
            success = result and result.startswith(expected_prefix)
        
        status = "PASS" if success else "FAIL"
        
        if success:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:60]}...")
        print(f"   Ожидалось: {expected_prefix}")
        print(f"   Получено: {result}")
        print(f"   Все детали: {details}")
    
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТ: Пройдено {passed}/{len(test_cases)}, Не пройдено {failed}")
    print(f"{'='*60}")


def test_sql_extraction():
    """Тест извлечения информации о SQL"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        ("SELECT * FROM users WHERE id=1", "SQL: SELECT"),
        ("INSERT INTO orders VALUES (...)", "SQL: INSERT"),
        ("PostgreSQL database connection", "SQL: PostgreSQL"),
        ("MySQL query execution", "SQL: MySQL"),
        ("UPDATE customers SET name='test'", "SQL: UPDATE"),
    ]
    
    print("\n" + "="*60)
    print("ТЕСТ ИЗВЛЕЧЕНИЯ ИНФОРМАЦИИ SQL")
    print("="*60)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        details = classifier.extract_detailed_info(text)
        result = details[0] if details else None
        
        status = "PASS" if result and expected in result else "FAIL"
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:50]}...")
        print(f"   Ожидалось: {expected}")
        print(f"   Получено: {result}")


def test_no_dates():
    """Проверка что даты больше не извлекаются"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        "Рабочий документ от 05.11.2025",
        "Отчет за период 01.01.2025 - 31.12.2025",
        "Дата создания: 04.11.2025",
    ]
    
    print("\n" + "="*60)
    print("ТЕСТ: ДАТЫ НЕ ДОЛЖНЫ ИЗВЛЕКАТЬСЯ")
    print("="*60)
    
    all_passed = True
    for i, text in enumerate(test_cases, 1):
        details = classifier.extract_detailed_info(text)
        
        has_date = any("Дата:" in d for d in details)
        status = "PASS" if not has_date else "FAIL"
        
        if has_date:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text}")
        print(f"   Детали: {details}")
    
    if all_passed:
        print("\nPASS: All date tests passed! Dates are not extracted.")
    else:
        print("\nFAIL: There are issues with date filtering.")


if __name__ == "__main__":
    test_1c_extraction()
    test_sql_extraction()
    test_no_dates()
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)
