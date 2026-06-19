"""
Скрипт быстрой настройки системы
Генерирует .env файл с безопасными учетными данными
"""
import hashlib
import os
import secrets


def generate_password_hash(password: str, salt: str = None) -> tuple[str, str]:
    """
    Генерирует хеш пароля и соль
    
    Args:
        password: Пароль в открытом виде
        salt: Соль (если None, генерируется случайно)
        
    Returns:
        Кортеж (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(32)
    
    password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    
    return password_hash, salt


def main():
    print("=" * 60)
    print("🔧 Настройка системы анализа скриншотов")
    print("=" * 60)
    print()
    
    # Запрос пароля
    print("Введите пароль для администратора (минимум 8 символов):")
    password = input("> ")
    
    if len(password) < 8:
        print("❌ Пароль слишком короткий!")
        return
    
    # Генерация хеша и соли
    print("\n⚙️  Генерация хеша пароля...")
    password_hash, salt = generate_password_hash(password)
    
    print(f"✓ Хеш создан")
    print(f"✓ Соль создана")
    
    # Создание .env файла
    env_content = f"""# Конфигурация системы анализа скриншотов
# Сгенерировано: {__file__}

ADMIN_PASSWORD_HASH={password_hash}
AUTH_SALT={salt}
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        print(f"\n⚠️  Файл .env уже существует!")
        overwrite = input("Перезаписать? (y/n): ")
        if overwrite.lower() != 'y':
            print("❌ Отменено пользователем")
            return
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ Файл .env создан: {env_path}")
    print()
    print("📋 Следующие шаги:")
    print("1. Проверьте docker-compose.yml и настройте путь к папке со скриншотами")
    print("2. Создайте структуру директорий: mkdir storage\\screenshots storage\\database incoming")
    print("3. Запустите систему: docker-compose up -d")
    print("4. Откройте браузер: http://localhost:8501")
    print(f"5. Войдите с паролем: {password}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Отменено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
