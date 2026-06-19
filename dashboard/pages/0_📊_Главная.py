import streamlit as st
from database import DatabaseManager
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Добавление пути для импорта
sys.path.insert(0, '/app')
from auth import require_auth, show_logout_button

st.set_page_config(page_title="Главная", page_icon="📊", layout="wide")
require_auth()

# Инициализация БД
db = DatabaseManager()

# Заголовок
st.title("📊 Общая статистика системы")

# Фильтры по датам
col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input(
        "📅 Дата от",
        value=datetime.now() - timedelta(days=7)
    )
with col2:
    date_to = st.date_input(
        "📅 Дата до",
        value=datetime.now()
    )

# Преобразование дат в строки
date_from_str = date_from.strftime('%Y-%m-%d')
date_to_str = date_to.strftime('%Y-%m-%d')

# Загрузка статистики
stats = db.get_productivity_stats(date_from_str, date_to_str)

# KPI карточки
st.markdown("### Ключевые показатели")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📸 Всего скриншотов",
        value=stats['total_screenshots'] or 0
    )

with col2:
    st.metric(
        label="✅ Продуктивных",
        value=stats['productive_count'] or 0,
        delta=None
    )

with col3:
    st.metric(
        label="❌ Непродуктивных",
        value=stats['unproductive_count'] or 0,
        delta=None
    )

with col4:
    total = stats['total_screenshots'] or 0
    productive = stats['productive_count'] or 0
    productivity_pct = (productive / total * 100) if total > 0 else 0
    st.metric(
        label="📈 Продуктивность",
        value=f"{productivity_pct:.1f}%"
    )

# График продуктивности по дням
st.markdown("---")
st.markdown("### 📉 Динамика продуктивности")

daily_data = db.get_daily_productivity(date_from_str, date_to_str)

if daily_data:
    fig = px.line(
        daily_data,
        x='date',
        y='productivity_percentage',
        title="Процент продуктивного времени по дням",
        labels={'date': 'Дата', 'productivity_percentage': 'Продуктивность (%)'},
        markers=True
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Нет данных за выбранный период")

# Рейтинг сотрудников
st.markdown("---")
st.markdown("### 🏆 Рейтинг сотрудников по продуктивности")

employee_ranking = db.get_employee_ranking(date_from_str, date_to_str)

if employee_ranking:
    # Создание DataFrame для отображения
    import pandas as pd
    df_ranking = pd.DataFrame(employee_ranking)
    
    # Переименование колонок для лучшего отображения
    df_ranking = df_ranking.rename(columns={
        'name': 'Сотрудник',
        'total_screenshots': 'Всего скриншотов',
        'productive_pct': 'Продуктивность (%)'
    })
    
    # Отображение таблицы
    st.dataframe(
        df_ranking,
        column_config={
            "Сотрудник": st.column_config.TextColumn("Сотрудник"),
            "Всего скриншотов": st.column_config.NumberColumn("Всего скриншотов"),
            "Продуктивность (%)": st.column_config.ProgressColumn(
                "Продуктивность",
                min_value=0,
                max_value=100,
                format="%f%%"
            ),
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("ℹ️ Нет данных для отображения рейтинга")

# Показ кнопки выхода
show_logout_button()
