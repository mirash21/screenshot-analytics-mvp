"""
Тест проверки работы с OCR ошибками распознавания
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_ocr_errors():
    """Проверка что приложения определяются несмотря на OCR ошибки"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст с ошибками, ожидаемое приложение)
        ("sberbankrofmainzul банк", "browser_work"),  # sberbank с ошибкой
        ("KonturScerepa Экстерн", "browser_work"),  # kontur с ошибкой
        ("Янеекебод ФД базы", "browser_work"),  # яндекс с ошибкой
        ("Googie Docs документ", "browser_work"),  # google с ошибкой
        ("Finkaper Tinkoff", "browser_work"),  # tinkoff с ошибкой
        ("diadoc-kontur.ru", "browser_work"),  # правильное написание
    ]
    
    print("="*60)
    print("ТЕСТ: РАСПОЗНАВАНИЕ С OCR ОШИБКАМИ")
    print("="*60)
    
    all_passed = True
    
    for i, (text, expected_app) in enumerate(test_cases, 1):
        detected = classifier.detect_applications(text)
        has_expected = expected_app in detected['work_apps']
        
        status = "PASS" if has_expected else "FAIL"
        
        if not has_expected:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:50]}")
        print(f"   Ожидалось: {expected_app}")
        print(f"   Рабочие: {detected['work_apps']}")
        print(f"   Детали: {detected['details']}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Все тесты пройдены! Система устойчива к OCR ошибкам.")
    else:
        print("❌ Есть проблемы с распознаванием")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_ocr_errors()
