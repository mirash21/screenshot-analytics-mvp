"""
Тест проверки что VK и другие приложения не определяются ложно
"""
import sys
sys.path.insert(0, 'ocr-analyzer')

from keyword_classifier import KeywordClassifier


class MockDB:
    """Mock database для тестирования"""
    def get_keywords(self, category):
        return []


def test_no_false_vk():
    """Проверка что VK не определяется в рабочих текстах"""
    classifier = KeywordClassifier(MockDB())
    
    # Тексты где VK НЕ должен определяться
    work_texts = [
        "Контакт с клиентом установлен",
        "Стена новостей компании",
        "Закладки в браузере Chrome",
        "Видео конференция Zoom",
        "Музыка в офисе играет",
        "Корзина товаров для заказа",
        "Фильм о бизнесе",
        "Сериал про работу",
        "Магазин канцтоваров",
        "Купить оборудование",
        "Скидка на поставки",
    ]
    
    print("="*60)
    print("ТЕСТ: ЛОЖНЫЕ СРАБАТЫВАНИЯ VK И ДРУГИХ ПРИЛОЖЕНИЙ")
    print("="*60)
    
    all_passed = True
    
    for i, text in enumerate(work_texts, 1):
        detected = classifier.detect_applications(text)
        
        has_vk = 'vk' in detected['work_apps'] or 'vk' in detected['unproductive_apps']
        has_youtube = 'youtube' in detected['work_apps'] or 'youtube' in detected['unproductive_apps']
        has_shopping = 'shopping' in detected['work_apps'] or 'shopping' in detected['unproductive_apps']
        
        false_positive = has_vk or has_youtube or has_shopping
        
        status = "PASS" if not false_positive else "FAIL"
        
        if false_positive:
            all_passed = False
            print(f"\n{i}. {status}")
            print(f"   Текст: {text}")
            print(f"   Рабочие: {detected['work_apps']}")
            print(f"   Личные: {detected['unproductive_apps']}")
            print(f"   Детали: {detected['details']}")
    
    if all_passed:
        print("\n✅ Все тесты пройдены! Нет ложных срабатываний.")
    else:
        print("\n❌ Обнаружены ложные срабатывания!")
    
    return all_passed


def test_no_false_work_apps():
    """Проверка что рабочие приложения не определяются ложно"""
    classifier = KeywordClassifier(MockDB())
    
    # Тексты где VSCode и другие НЕ должны определяться
    general_texts = [
        "Написать код программы",  # не vscode
        "Терминал для команд",  # не vscode
        "Файл script.py создан",  # не vscode
        "Открыть файл document.js",  # не vscode
        "Java разработка",  # не vscode
        "Лид в воронке продаж",  # не bitrix
        "Сделка с клиентом",  # не bitrix
        "Спринт по методологии",  # не jira
        "Бэклог задач",  # не jira
        "Канал связи",  # не slack
        "Команда разработчиков",  # не slack
        "Звонок с партнером",  # не teams
        "Конференция Zoom",  # не teams (но zoom может быть)
        "Банковская транзакция",  # не sap
        "SQL запрос к базе данных",  # не sql
        "Презентация проекта",  # не powerpoint
        "Письмо клиенту",  # не outlook
        "Входящее сообщение",  # не outlook
    ]
    
    print("\n" + "="*60)
    print("ТЕСТ: ЛОЖНЫЕ СРАБАТЫВАНИЯ РАБОЧИХ ПРИЛОЖЕНИЙ")
    print("="*60)
    
    all_passed = True
    
    for i, text in enumerate(general_texts, 1):
        detected = classifier.detect_applications(text)
        
        # Проверяем что не определились приложения по общим словам
        false_apps = []
        if 'vscode' in detected['work_apps'] and any(w in text.lower() for w in ['код', 'терминал', '.py', '.js', 'java']):
            false_apps.append('vscode')
        if 'jira' in detected['work_apps'] and any(w in text.lower() for w in ['спринт', 'бэклог']):
            false_apps.append('jira')
        if 'slack' in detected['work_apps'] and any(w in text.lower() for w in ['канал', 'команда']):
            false_apps.append('slack')
        if 'teams' in detected['work_apps'] and any(w in text.lower() for w in ['звонок', 'конференция']):
            false_apps.append('teams')
        if 'sql' in detected['work_apps'] and any(w in text.lower() for w in ['запрос', 'база данных']):
            false_apps.append('sql')
        if 'powerpoint' in detected['work_apps'] and 'презентация' in text.lower():
            false_apps.append('powerpoint')
        if 'outlook' in detected['work_apps'] and any(w in text.lower() for w in ['письмо', 'входящее']):
            false_apps.append('outlook')
        
        if false_apps:
            all_passed = False
            print(f"\n{i}. FAIL")
            print(f"   Текст: {text}")
            print(f"   Ложно определены: {false_apps}")
            print(f"   Рабочие: {detected['work_apps']}")
    
    if all_passed:
        print("\n✅ Все тесты пройдены! Нет ложных срабатываний рабочих приложений.")
    else:
        print("\n❌ Обнаружены ложные срабатывания рабочих приложений!")
    
    return all_passed


def test_true_vk_detection():
    """Проверка что VK правильно определяется когда есть"""
    classifier = KeywordClassifier(MockDB())
    
    vk_texts = [
        "vk.com/id123456",
        "vk.com/feed",
        "vkontakte.ru/messages",
    ]
    
    print("\n" + "="*60)
    print("ТЕСТ: ПРАВИЛЬНОЕ ОПРЕДЕЛЕНИЕ VK")
    print("="*60)
    
    all_passed = True
    
    for i, text in enumerate(vk_texts, 1):
        detected = classifier.detect_applications(text)
        
        has_vk = 'vk' in detected['unproductive_apps']
        
        status = "PASS" if has_vk else "FAIL"
        
        if not has_vk:
            all_passed = False
        
        print(f"\n{i}. {status}")
        print(f"   Текст: {text}")
        print(f"   Личные: {detected['unproductive_apps']}")
    
    if all_passed:
        print("\n✅ VK правильно определяется.")
    else:
        print("\n❌ VK не определяется когда должен!")
    
    return all_passed


if __name__ == "__main__":
    result1 = test_no_false_vk()
    result2 = test_no_false_work_apps()
    result3 = test_true_vk_detection()
    
    print("\n" + "="*60)
    if result1 and result2 and result3:
        print("ИТОГ: ВСЕ ТЕСТЫ ПРОЙДЕНЫ ✅")
    else:
        print("ИТОГ: ЕСТЬ ПРОБЛЕМЫ ❌")
    print("="*60)
