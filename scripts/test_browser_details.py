"""
Тест проверки детализации browser_work сервисов
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_browser_service_details():
    """Проверка что browser_work показывает конкретный сервис"""
    classifier = KeywordClassifier(MockDB())
    
    test_cases = [
        # (OCR текст, ожидаемый результат)
        ("diadoc-kontur.ru документы", "Рабочие: Диадок"),
        ("Контур.Экстерн отчетность", "Рабочие: Контур"),
        ("СБЕРБАНК платеж перевод", "Рабочие: Сбербанк"),
        ("Finkoper Tinkoff банк", "Рабочие: Тинькофф"),
        ("WhatsApp Web чат", "Рабочие: WhatsApp"),
        ("Яндекс.ФД УСН базы", "Рабочие: Яндекс"),
        ("Google Docs документ", "Рабочие: Google"),
        ("Реквизит ИФНС код", "Рабочие: ФНС"),
        ("Инфо Трейд система", "Рабочие: Инфо Трейд"),
    ]
    
    print("="*60)
    print("ТЕСТ: ДЕТАЛИЗАЦИЯ BROWSER_WORK СЕРВИСОВ")
    print("="*60)
    
    all_passed = True
    
    for i, (text, expected_detail) in enumerate(test_cases, 1):
        details = classifier.build_details(text)
        has_expected = expected_detail in details
        
        # Проверяем что НЕТ дублирования "browser_work:"
        has_duplicate = "browser_work:" in details or (details.count("browser_work") > 1)
        
        status = "PASS" if (has_expected and not has_duplicate) else "FAIL"
        
        if not (has_expected and not has_duplicate):
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text[:50]}")
        print(f"   Ожидалось: {expected_detail}")
        print(f"   Результат: {details}")
        if has_duplicate:
            print(f"   ⚠️  ПРЕДУПРЕЖДЕНИЕ: Обнаружено дублирование!")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Все тесты пройдены!")
    else:
        print("❌ Есть проблемы с детализацией")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_browser_service_details()
