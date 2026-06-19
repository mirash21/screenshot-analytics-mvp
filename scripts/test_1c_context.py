"""
Тест проверки определения 1С через контекст без явного "1С"
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_1c_context_detection():
    """Проверка что 1С определяется даже когда OCR плохо распознал "1С" """
    classifier = KeywordClassifier(MockDB())
    
    # Тексты где "1С" может быть плохо распознано но есть контекст
    test_cases = [
        # (OCR текст, должно определить 1С)
        ("МАА-Бухгалтерия базовая Счета покупателям", True),
        ("Бухгалтерия предприятия Реализация товаров", True),
        ("Счета покупателям Накладная Бухгалтерия", True),
        ("1С:Предприятие Бухгалтерия", True),  # Явное 1С
        ("Просто счет без контекста", False),  # Нет контекста 1С
        ("Обычная бухгалтерия отчет", False),  # Нет документов 1С
    ]
    
    print("="*60)
    print("ТЕСТ: ОПРЕДЕЛЕНИЕ 1С ЧЕРЕЗ КОНТЕКСТ")
    print("="*60)
    
    all_passed = True
    
    for i, (text, should_detect_1c) in enumerate(test_cases, 1):
        detected = classifier.detect_applications(text)
        has_1c = '1c' in detected['work_apps']
        
        status = "PASS" if has_1c == should_detect_1c else "FAIL"
        
        if has_1c != should_detect_1c:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:60]}")
        print(f"   Ожидалось 1С: {should_detect_1c}")
        print(f"   Определено 1С: {has_1c}")
        print(f"   Рабочие: {detected['work_apps']}")
        print(f"   Детали: {detected['details']}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Все тесты пройдены!")
    else:
        print("❌ Есть проблемы с определением 1С")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_1c_context_detection()
