"""
Парсер путей к скриншотам
Ожидает структуру: Имя_Сотрудника/ГГГГММДД/ЧЧММСС.jpeg
"""
import os
from datetime import datetime


def parse_screenshot_path(file_path: str) -> dict:
    """
    Парсит путь к скриншоту.
    
    Поддерживаемые форматы:
    1. Гульнара/20251105/084053.jpeg (файл с именем времени)
    2. Гульнара/20251105/084053/084054325.jpg (папка с временем, файл с HHMMSSmmm)
    
    Args:
        file_path: Полный путь к файлу скриншота
        
    Returns:
        Dictionary с ключами:
            - employee_name: имя сотрудника
            - date: дата в формате YYYY-MM-DD
            - time: время в формате HH:MM:SS
            - filename: имя файла с расширением
    """
    # Нормализация пути
    file_path = os.path.normpath(file_path)
    
    # Извлечение имени файла
    filename = os.path.basename(file_path)
    
    # Получение родительских директорий
    parent_dir = os.path.dirname(file_path)
    parent_name = os.path.basename(parent_dir)
    
    grandparent_dir = os.path.dirname(parent_dir)
    grandparent_name = os.path.basename(grandparent_dir)
    
    great_grandparent_dir = os.path.dirname(grandparent_dir)
    employee_name = os.path.basename(great_grandparent_dir)
    
    # Проверяем формат: если parent_name это время (6 цифр), то это новый формат
    # Структура: employee/date/time_folder/filename
    if len(parent_name) == 6 and parent_name.isdigit():
        # Новый формат: папка с временем
        time_folder = parent_name
        date_dir = grandparent_name
        
        # Извлекаем время из имени файла (первые 6 цифр)
        time_str_raw = os.path.splitext(filename)[0][:6]
    else:
        # Старый формат: файл с временем
        # Структура: employee/date/filename
        time_str_raw = parent_name
        date_dir = grandparent_name
    
    # Парсинг даты из формата ГГГГММДД
    try:
        date_obj = datetime.strptime(date_dir, '%Y%m%d')
        date_str = date_obj.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Неверный формат даты в пути: {date_dir}. Ожидается ГГГГММДД")
    
    # Парсинг времени
    try:
        time_obj = datetime.strptime(time_str_raw, '%H%M%S')
        time_str = time_obj.strftime('%H:%M:%S')
    except ValueError:
        raise ValueError(f"Неверный формат времени: {time_str_raw}. Ожидается ЧЧММСС")
    
    return {
        'employee_name': employee_name,
        'date': date_str,
        'time': time_str,
        'filename': filename
    }


def validate_screenshot_format(file_path: str) -> bool:
    """
    Проверяет, соответствует ли путь ожидаемому формату
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если формат корректен, False иначе
    """
    try:
        parse_screenshot_path(file_path)
        return True
    except (ValueError, IndexError):
        return False
