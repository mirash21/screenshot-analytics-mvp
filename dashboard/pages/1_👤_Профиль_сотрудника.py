import streamlit as st
from database import DatabaseManager
from datetime import datetime
import sys
import os

# Добавление пути для импорта
sys.path.insert(0, '/app')
from auth import require_auth, show_logout_button

st.set_page_config(page_title="Профиль сотрудника", page_icon="👤")
require_auth()

# Инициализация БД
db = DatabaseManager()

# Заголовок
st.title("👤 Профиль сотрудника")

# Выбор сотрудника
employees = db.get_all_employees()

if not employees:
    st.warning("⚠️ В системе еще нет зарегистрированных сотрудников")
    show_logout_button()
    st.stop()

employee_names = [emp['name'] for emp in employees]
selected_employee = st.selectbox("Выберите сотрудника", employee_names)

if selected_employee:
    employee_id = db.get_employee_id(selected_employee)
    
    # Фильтр по дате
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_date = st.date_input("📅 Дата", value=datetime.now())
    
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    
    # Загрузка скриншотов
    screenshots = db.get_employee_screenshots(employee_id, selected_date_str)
    
    if not screenshots:
        st.info(f"ℹ️ Нет данных за {selected_date_str}")
    else:
        # Статистика за день
        total = len(screenshots)
        productive = sum(1 for s in screenshots if s['category'] in ('work', 'productive'))
        unproductive = sum(1 for s in screenshots if s['category'] in ('user', 'unproductive'))
        unknown = sum(1 for s in screenshots if s['category'] in ('unknown', None) or s['category'] not in ('work', 'productive', 'user', 'unproductive'))
        
        st.markdown("### 📊 Статистика за день")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего скриншотов", total)
        with col2:
            st.metric("✅ Продуктивных", productive)
        with col3:
            st.metric("❌ Непродуктивных", unproductive)
        with col4:
            st.metric("⚪ Не определено", unknown)
        
        # Прогресс-бар продуктивности
        productivity_pct = (productive / total * 100) if total > 0 else 0
        st.progress(productivity_pct / 100)
        st.caption(f"Уровень продуктивности: {productivity_pct:.1f}%")
        
        # Лента скриншотов с цветовой маркировкой
        st.markdown("---")
        st.markdown("### 🖼️ Лента скриншотов")
        
        for idx, screenshot in enumerate(screenshots):
            # Определение цвета и иконки
            category = screenshot.get('category', 'unknown')
            confidence = screenshot.get('confidence', 0.0)
            
            if category in ('work', 'productive'):
                color = "🟢"
                badge = "Работа"
            elif category in ('user', 'unproductive'):
                color = "🔴"
                badge = "Личное"
            else:
                color = "⚪"
                badge = "Не определено"
            
            # Создание карточки скриншота
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    st.markdown(f"### {color}")
                    st.write(f"**{screenshot['capture_time']}**")
                    st.caption(badge)
                    if confidence and confidence > 0:
                        st.caption(f"Уверенность: {confidence:.0%}")
                
                with col2:
                    # Отображение изображения
                    file_path = screenshot['file_path']
                    if os.path.exists(file_path):
                        try:
                            st.image(file_path, width=400)
                        except Exception as e:
                            st.error(f"Ошибка загрузки изображения: {e}")
                    else:
                        st.warning("⚠️ Файл не найден")
                
                with col3:
                    details = screenshot.get('details', '')
                    if details:
                        st.caption("🔍 Детали:")
                        st.write(details)
                    
                    # Распознанный текст
                    ocr_text = screenshot.get('ocr_text', '')
                    if ocr_text:
                        st.caption("📝 Распознанный текст:")
                        with st.expander("Показать текст", expanded=False):
                            st.text_area(
                                "",
                                value=ocr_text,
                                height=150,
                                disabled=True,
                                key=f"text_{screenshot['id']}"
                            )
                    else:
                        st.caption("Текст не распознан")
                
                st.divider()

# Показ кнопки выхода
show_logout_button()
