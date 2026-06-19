"""
Главная точка входа приложения Streamlit
Перенаправляет на страницу авторизации или главную страницу
"""
import streamlit as st
import sys
import os

sys.path.insert(0, '/app')
from auth import require_auth, show_logout_button

# Проверка авторизации
require_auth()

# Перенаправление на главную страницу
st.switch_page("pages/0_📊_Главная.py")
