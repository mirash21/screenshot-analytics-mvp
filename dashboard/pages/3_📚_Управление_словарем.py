import streamlit as st
from database import DatabaseManager
import sys
import os

sys.path.insert(0, '/app')
from auth import require_auth, show_logout_button

st.set_page_config(page_title="Управление словарем", page_icon="📚")
require_auth()

db = DatabaseManager()

st.title("📚 Управление словарем ключевых слов")
st.markdown("Настройка категорий для классификации скриншотов")

# Табы
tab1, tab2 = st.tabs(["✅ Рабочие слова", "❌ Личные слова"])

with tab1:
    st.subheader("Рабочие ключевые слова")
    
    productive_words = db.get_keywords('work')
    st.write(f"**Всего слов:** {len(productive_words)}")
    
    if productive_words:
        st.write(", ".join(sorted(productive_words)))
    
    # Добавление нового слова
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_word = st.text_input("Добавить новое слово", key="add_prod", placeholder="Например: 1с")
    with col2:
        if st.button("➕ Добавить", key="btn_add_prod", use_container_width=True):
            if new_word:
                db.add_keyword(new_word.lower(), 'work')
                st.success(f"✅ Добавлено: {new_word}")
                st.rerun()
            else:
                st.warning("Введите слово")
    
    # Удаление слова
    if productive_words:
        st.markdown("---")
        word_to_delete = st.selectbox("Удалить слово", productive_words, key="del_prod")
        if st.button("🗑️ Удалить", key="btn_del_prod"):
            db.delete_keyword(word_to_delete)
            st.success(f"🗑️ Удалено: {word_to_delete}")
            st.rerun()

with tab2:
    st.subheader("Личные ключевые слова")
    
    unproductive_words = db.get_keywords('user')
    st.write(f"**Всего слов:** {len(unproductive_words)}")
    
    if unproductive_words:
        st.write(", ".join(sorted(unproductive_words)))
    
    # Добавление нового слова
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_word = st.text_input("Добавить новое слово", key="add_unprod", placeholder="Например: youtube")
    with col2:
        if st.button("➕ Добавить", key="btn_add_unprod", use_container_width=True):
            if new_word:
                db.add_keyword(new_word.lower(), 'user')
                st.success(f"✅ Добавлено: {new_word}")
                st.rerun()
            else:
                st.warning("Введите слово")
    
    # Удаление слова
    if unproductive_words:
        st.markdown("---")
        word_to_delete = st.selectbox("Удалить слово", unproductive_words, key="del_unprod")
        if st.button("🗑️ Удалить", key="btn_del_unprod"):
            db.delete_keyword(word_to_delete)
            st.success(f"🗑️ Удалено: {word_to_delete}")
            st.rerun()

# Загрузка стандартных слов
st.markdown("---")
st.subheader("⚙️ Системные настройки")

if st.button("📥 Загрузить стандартный словарь", use_container_width=True):
    db.load_default_keywords()
    st.success("✅ Стандартный словарь загружен!")
    st.rerun()

show_logout_button()
