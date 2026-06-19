"""
Тест проверки определения российских бизнес-терминов
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_russian_business_terms():
    """Проверка определения российских бизнес-сервисов и терминов"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст, ожидаемое приложение)
        ("СБЕРБАНК платеж перевод", "browser_work"),
        ("Реквизит ИФНС код", "browser_work"),
        ("Налоговая инспекция документы", "browser_work"),
        ("ФНС России отчет", "browser_work"),
        ("Инфо Трейд система", "browser_work"),
        ("1С ИНФО Трэйд предприятие", "browser_work"),
    ]
    
    print("="*60)
    print("ТЕСТ: РОССИЙСКИЕ БИЗНЕС-ТЕРМИНЫ")
    print("="*60)
    
    all_passed = True
    
    for i, (text, expected_app) in enumerate(test_cases, 1):
        detected = classifier.detect_applications(text)
        has_expected = expected_app in detected['work_apps']
        
        status = "PASS" if has_expected else "FAIL"
        
        if not has_expected:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text}")
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
    test_russian_business_terms()
