"""
Модуль авторизации для дашборда
"""
import streamlit as st
import hashlib
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH, AUTH_SALT


def hash_password(password: str) -> str:
    """
    Хеширование пароля с солью
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        SHA256 хеш пароля
    """
    salt = AUTH_SALT
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def check_credentials(username: str, password: str) -> bool:
    """
    Проверка учетных данных пользователя
    
    Args:
        username: Имя пользователя
        password: Пароль
        
    Returns:
        True если credentials верны, False иначе
    """
    # Проверка имени пользователя
    if username != ADMIN_USERNAME:
        return False
    
    # Если хеш пароля не установлен, используем дефолтный пароль 'admin'
    expected_hash = ADMIN_PASSWORD_HASH if ADMIN_PASSWORD_HASH else hash_password('admin')
    
    # Проверка хеша пароля
    return hash_password(password) == expected_hash


def login_page():
    """Отображение страницы входа"""
    # set_page_config уже вызван в основном файле страницы
    
    # Центрирование формы
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Вход в систему")
        st.markdown("---")
        
        username = st.text_input("Логин", placeholder="Введите логин")
        password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
        
        if st.button("Войти", type="primary", use_container_width=True):
            if username and password:
                if check_credentials(username, password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("❌ Неверный логин или пароль")
            else:
                st.warning("⚠️ Пожалуйста, заполните все поля")


def require_auth():
    """
    Декоратор для защиты страниц авторизацией
    Если пользователь не аутентифицирован, показывает страницу входа
    """
    if not st.session_state.get('authenticated', False):
        login_page()
        st.stop()


def logout():
    """Выход из системы"""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.rerun()


def show_logout_button():
    """Отображение кнопки выхода в sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **{st.session_state.get('username', 'User')}**")
    
    if st.sidebar.button("🚪 Выйти", use_container_width=True):
        logout()
