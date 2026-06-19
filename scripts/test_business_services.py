"""
Тест проверки определения Kontur, Diadoc и других бизнес-сервисов
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_business_services():
    """Проверка определения российских бизнес-сервисов"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст, ожидаемое приложение)
        ("Контур.Экстерн отчетность", "browser_work"),
        ("diadoc-kontur.ru документы", "browser_work"),
        ("Яндекс.ФД УСН базы", "browser_work"),
        ("Google Docs документ", "browser_work"),
        ("Finkoper Tinkoff банк", "browser_work"),
        ("WhatsApp Web чат", "browser_work"),
    ]
    
    print("="*60)
    print("ТЕСТ: ОПРЕДЕЛЕНИЕ БИЗНЕС-СЕРВИСОВ")
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
        print("✅ Все тесты пройдены!")
    else:
        print("❌ Есть проблемы с определением")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_business_services()
