import streamlit as st
from database import DatabaseManager
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/app')
from auth import require_auth, show_logout_button

st.set_page_config(page_title="Лента нарушений", page_icon="🚨", layout="wide")
require_auth()

db = DatabaseManager()

st.title("🚨 Лента нарушений")
st.markdown("Скриншоты с непродуктивной активностью сотрудников")

# Фильтры
col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("Период от", value=datetime.now() - timedelta(days=7))
with col2:
    date_to = st.date_input("Период до", value=datetime.now())

date_from_str = date_from.strftime('%Y-%m-%d')
date_to_str = date_to.strftime('%Y-%m-%d')

# Загрузка нарушений
violations = db.get_unproductive_screenshots(date_from_str, date_to_str)

st.markdown(f"**Найдено нарушений:** {len(violations)}")

if not violations:
    st.success("✅ Нарушений за выбранный период не обнаружено!")
else:
    for violation in violations:
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.markdown(f"### 🔴 {violation['employee_name']}")
                st.caption(f"📅 {violation['capture_date']}")
                st.caption(f"⏰ {violation['capture_time']}")
                if violation.get('confidence'):
                    st.caption(f"Уверенность: {violation['confidence']:.0%}")
            
            with col2:
                file_path = violation['file_path']
                if os.path.exists(file_path):
                    try:
                        st.image(file_path, width=450)
                    except:
                        st.error("Ошибка загрузки")
                else:
                    st.warning("Файл не найден")
            
            with col3:
                details = violation.get('details', '')
                if details:
                    st.caption("🔍 Детали:")
                    st.write(details)
                
                ocr_text = violation.get('ocr_text', '')
                if ocr_text:
                    st.caption("📝 Распознанный текст:")
                    with st.expander("Показать текст"):
                        st.text_area(
                            "",
                            value=ocr_text[:300] + ("..." if len(ocr_text) > 300 else ""),
                            height=120,
                            disabled=True,
                            key=f"text_{violation['id']}"
                        )
            
            st.divider()

show_logout_button()
