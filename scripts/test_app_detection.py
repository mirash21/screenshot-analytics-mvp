"""
Тест проверки определения приложений через контекст
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    """Mock database для тестирования"""
    def get_keywords(self, category):
        # Возвращаем ключевые слова из БД для классификации
        if category == 'work':
            return ['бухгалтерия', 'счета', 'накладная', 'отчет', 'документ']
        elif category == 'user':
            return []
        return []


def test_1c_context_detection():
    """Проверка что 1С определяется через контекст даже без ключевого слова '1c'"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст, должно определить 1С)
        ("Бухгалтерия предприятия Счета покупателям", True),
        ("1С: Предприятие Пользователь: Иванова Н.Н.", True),
        ("ИНФО Трэйд (1С Предприятие)", True),
        ("Реализация товаров и услуг Счет-фактура", True),
        ("Простой рабочий документ", False),  # Нет признаков 1С
        ("Отчет за месяц подготовлен", False),  # Общие слова
    ]
    
    print("="*60)
    print("ТЕСТ: ОПРЕДЕЛЕНИЕ 1С ЧЕРЕЗ КОНТЕКСТ")
    print("="*60)
    
    all_passed = True
    
    for i, (text, should_detect_1c) in enumerate(test_cases, 1):
        details = classifier.build_details(text)
        has_1c = '1c' in details.lower() or '1С' in details
        
        passed = (has_1c == should_detect_1c)
        status = "PASS" if passed else "FAIL"
        
        if not passed:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:60]}")
        print(f"   Ожидалось 1С: {should_detect_1c}")
        print(f"   Определено 1С: {has_1c}")
        print(f"   Детали: {details}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Все тесты пройдены!")
    else:
        print("❌ Есть проблемы с определением 1С")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_1c_context_detection()
