"""
Тест проверки что Bitrix не определяется ложно
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    def get_keywords(self, category):
        return []


def test_bitrix_false_positives():
    """Проверка что Bitrix не определяется в текстах где его нет"""
    classifier = KeywordClassifier(MockDB())
    
    # Тексты где НЕ должно быть Bitrix
    false_positive_texts = [
        "МИНА РИКС платеж",  # OCR ошибка - не Bitrix
        "webchat2desk.com чат",  # Чат сервис - не Bitrix
        "РИКС банк перевод",  # Другое слово - не Bitrix
        "matrix система",  # Содержит "trix" но это matrix - не Bitrix
    ]
    
    # Тексты где ДОЛЖЕН быть Bitrix
    true_positive_texts = [
        "bitrix24 CRM система",
        "Битрикс управление сайтом",
        "1C-Bitrix интеграция",
        "bitrix портал",
    ]
    
    print("="*60)
    print("ТЕСТ: BITRIX FALSE POSITIVES")
    print("="*60)
    
    all_passed = True
    
    print("\n--- Проверка ЛОЖНЫХ срабатываний (должно быть PASS) ---\n")
    for i, text in enumerate(false_positive_texts, 1):
        detected = classifier.detect_applications(text)
        has_bitrix = 'bitrix' in detected['work_apps']
        
        status = "PASS" if not has_bitrix else "FAIL"
        
        if has_bitrix:
            all_passed = False
        
        print(f"{i}. {status}")
        print(f"   Текст: {text}")
        print(f"   Рабочие приложения: {detected['work_apps']}")
        print()
    
    print("--- Проверка ПРАВИЛЬНЫХ срабатываний (должно быть PASS) ---\n")
    for i, text in enumerate(true_positive_texts, 1):
        detected = classifier.detect_applications(text)
        has_bitrix = 'bitrix' in detected['work_apps']
        
        status = "PASS" if has_bitrix else "FAIL"
        
        if not has_bitrix:
            all_passed = False
        
        print(f"{i}. {status}")
        print(f"   Текст: {text}")
        print(f"   Рабочие приложения: {detected['work_apps']}")
        print()
    
    print("="*60)
    if all_passed:
        print("✅ Все тесты пройдены!")
    else:
        print("❌ Есть проблемы с определением Bitrix")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    test_bitrix_false_positives()
