# dashboard.py - Интерактивный дашборд для анализа пожертвований

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="Анализ пожертвований фонда",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок дашборда
st.title("❤️ Аналитический дашборд пожертвований")
st.markdown("---")

# Загрузка данных
@st.cache_data
def load_data():
    # Используем raw-строку для пути (r"путь") или заменяем \ на /
    # Вариант 1: используем двойные обратные слэши
    file_path = r"G:\Мой диск\Обучение\Яндекс.Практикум\Мастерская_Марафон добра\Subscription_analysis_dashbord\encoded_Подписки Cloud Payments 18-06.csv"
    
    # Вариант 2: используем обычные слэши (рекомендуется)
    # file_path = "G:/Мой диск/Обучение/Яндекс.Практикум/Мастерская_Марафон добра/Subscription_analysis_dashbord/encoded_Подписки Cloud Payments 18-06.csv"
    
    # Читаем CSV с правильным разделителем и преобразованием чисел
    df = pd.read_csv(
        file_path, 
        delimiter=';',
        decimal=',',  # Важно! Указываем, что десятичный разделитель - запятая
        parse_dates=['Дата/время создания', 'Дата/время последнего платежа', 'Дата/время следующего платежа']
    )
    
    # Добавляем полезные колонки
    df['Дата'] = df['Дата/время создания'].dt.date
    df['Год_месяц'] = df['Дата/время создания'].dt.to_period('M')
    df['Месяц'] = df['Дата/время создания'].dt.month
    df['Год'] = df['Дата/время создания'].dt.year
    df['День_недели'] = df['Дата/время создания'].dt.dayofweek
    df['Час'] = df['Дата/время создания'].dt.hour
    
    # Убеждаемся, что сумма - числовой тип
    df['Сумма'] = df['Сумма'].astype(float)
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Файл с данными не найден!")
    st.info("""
    Проверьте путь к файлу. Возможные проблемы:
    1. Файл не существует по указанному пути
    2. В пути есть русские буквы или пробелы (это может вызывать проблемы)
    
    Рекомендую:
    - Поместить файл в папку с проектом
    - Использовать относительный путь: `data/encoded_Подписки Cloud Payments 18-06.csv`
    """)
    st.stop()

# Боковая панель с фильтрами
st.sidebar.title("🔍 Фильтры")

# Фильтр по дате
min_date = df['Дата'].min()
max_date = df['Дата'].max()
date_range = st.sidebar.date_input(
    "Период",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df['Дата'] >= start_date) & (df['Дата'] <= end_date)]
else:
    df_filtered = df

# Фильтр по статусу
status_options = ['Все'] + sorted(df['Статус'].unique().tolist())
selected_status = st.sidebar.selectbox("Статус подписки", status_options)

if selected_status != 'Все':
    df_filtered = df_filtered[df_filtered['Статус'] == selected_status]

# Фильтр по сумме
min_amount = float(df['Сумма'].min())
max_amount = float(df['Сумма'].max())
amount_range = st.sidebar.slider(
    "Сумма пожертвования",
    min_value=min_amount,
    max_value=max_amount,
    value=(min_amount, max_amount)
)

df_filtered = df_filtered[(df_filtered['Сумма'] >= amount_range[0]) & 
                          (df_filtered['Сумма'] <= amount_range[1])]

# Основные KPI
st.markdown("## 📊 Ключевые показатели")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Всего донаторов", df_filtered['ID плательщика'].nunique())

with col2:
    st.metric("Всего подписок", len(df_filtered))

with col3:
    total_amount = df_filtered['Сумма'].sum()
    st.metric("Общая сумма", f"{total_amount:,.0f} ₽")

with col4:
    avg_check = df_filtered['Сумма'].mean()
    st.metric("Средний чек", f"{avg_check:,.0f} ₽")

with col5:
    active_subs = df_filtered[df_filtered['Статус'].isin(['Активна', 'Просрочена'])].shape[0]
    active_pct = active_subs / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
    st.metric("Активные подписки", f"{active_pct:.1f}%")

st.markdown("---")

# Графики в два столбца
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Динамика пожертвований")
    
    # Группировка по месяцам
    monthly_data = df_filtered.groupby('Год_месяц').agg({
        'Сумма': 'sum',
        'ID': 'count'
    }).reset_index()
    monthly_data['Год_месяц'] = monthly_data['Год_месяц'].astype(str)
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    # Столбцы для суммы
    ax1.bar(monthly_data['Год_месяц'], monthly_data['Сумма'], 
            color='steelblue', alpha=0.7, label='Сумма')
    ax1.set_xlabel('Месяц')
    ax1.set_ylabel('Сумма (₽)', color='steelblue')
    ax1.tick_params(axis='x', rotation=45)
    
    # Линия для количества подписок
    ax2 = ax1.twinx()
    ax2.plot(monthly_data['Год_месяц'], monthly_data['ID'], 
             color='coral', marker='o', linewidth=2, label='Количество')
    ax2.set_ylabel('Количество подписок', color='coral')
    ax2.tick_params(axis='y', labelcolor='coral')
    
    plt.title('Динамика пожертвований по месяцам')
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.markdown("### 🥧 Распределение по статусам")
    
    status_counts = df_filtered['Статус'].value_counts()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#2ecc71', '#f1c40f', '#e74c3c', '#3498db', '#95a5a6']
    ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', 
           colors=colors[:len(status_counts)])
    ax.set_title('Распределение подписок по статусам')
    st.pyplot(fig)

# Второй ряд графиков
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 📊 Распределение сумм пожертвований")
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Ограничиваем для наглядности
    max_amount_display = df_filtered['Сумма'].quantile(0.95)
    filtered_amounts = df_filtered[df_filtered['Сумма'] <= max_amount_display]['Сумма']
    
    ax.hist(filtered_amounts, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axvline(filtered_amounts.mean(), color='red', linestyle='--', 
               linewidth=2, label=f'Среднее: {filtered_amounts.mean():.0f}')
    ax.axvline(filtered_amounts.median(), color='green', linestyle='--', 
               linewidth=2, label=f'Медиана: {filtered_amounts.median():.0f}')
    ax.set_xlabel('Сумма (₽)')
    ax.set_ylabel('Количество подписок')
    ax.legend()
    ax.set_title('Распределение сумм пожертвований')
    st.pyplot(fig)

with col4:
    st.markdown("### 📅 Сезонность по месяцам")
    
    monthly_seasonal = df_filtered.groupby('Месяц').agg({
        'Сумма': ['mean', 'sum'],
        'ID': 'count'
    }).reset_index()
    monthly_seasonal.columns = ['Месяц', 'Средняя_сумма', 'Общая_сумма', 'Количество']
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(monthly_seasonal['Месяц'], monthly_seasonal['Средняя_сумма'], 
           color='coral', alpha=0.7)
    ax.set_xlabel('Месяц')
    ax.set_ylabel('Средняя сумма (₽)')
    ax.set_title('Сезонность: средняя сумма по месяцам')
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                        'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'])
    st.pyplot(fig)

# Третий ряд - топ донаторов и таблица
st.markdown("---")
st.markdown("## 🏆 Топ донаторов")

col5, col6 = st.columns(2)

with col5:
    # Топ-10 донаторов по сумме
    top_donors = df_filtered.groupby('ID плательщика').agg({
        'Сумма': 'sum',
        'ID': 'count'
    }).reset_index()
    top_donors.columns = ['ID плательщика', 'Общая_сумма', 'Количество_подписок']
    top_donors = top_donors.sort_values('Общая_сумма', ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top_donors['ID плательщика'].astype(str), top_donors['Общая_сумма'], 
            color='royalblue', alpha=0.8)
    ax.set_xlabel('Общая сумма (₽)')
    ax.set_title('Топ-10 донаторов по сумме')
    st.pyplot(fig)

with col6:
    st.markdown("### 📋 Последние подписки")
    recent_subs = df_filtered.sort_values('Дата/время создания', ascending=False).head(10)
    st.dataframe(
        recent_subs[['ID', 'Дата/время создания', 'Статус', 'Сумма', 'ID плательщика']],
        use_container_width=True,
        hide_index=True
    )

# Четвертый ряд - дополнительные метрики
st.markdown("---")
st.markdown("## 📈 Дополнительный анализ")

col7, col8, col9 = st.columns(3)

with col7:
    # Распределение по дням недели
    weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    weekday_counts = df_filtered['День_недели'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(weekday_names, weekday_counts.values, color='steelblue', alpha=0.7)
    ax.set_xlabel('День недели')
    ax.set_ylabel('Количество подписок')
    ax.set_title('Активность по дням недели')
    st.pyplot(fig)

with col8:
    # Распределение по часам
    hour_counts = df_filtered['Час'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(hour_counts.index, hour_counts.values, color='coral', alpha=0.7)
    ax.set_xlabel('Час')
    ax.set_ylabel('Количество подписок')
    ax.set_title('Активность по часам')
    st.pyplot(fig)

with col9:
    st.markdown("### 📊 Статистика по статусам")
    
    status_stats = df_filtered.groupby('Статус').agg({
        'Сумма': ['count', 'mean', 'sum']
    }).round(2)
    status_stats.columns = ['Количество', 'Средняя_сумма', 'Общая_сумма']
    status_stats['Доля_%'] = status_stats['Количество'] / status_stats['Количество'].sum() * 100
    
    st.dataframe(
        status_stats,
        use_container_width=True,
        column_config={
            "Количество": st.column_config.NumberColumn("Количество", format="%d"),
            "Средняя_сумма": st.column_config.NumberColumn("Средняя сумма", format="%.0f ₽"),
            "Общая_сумма": st.column_config.NumberColumn("Общая сумма", format="%.0f ₽"),
            "Доля_%": st.column_config.NumberColumn("Доля", format="%.1f%%")
        }
    )

# Пятый ряд - скачивание данных
st.markdown("---")
st.markdown("## 📥 Экспорт данных")

if st.button("Скачать отфильтрованные данные (CSV)"):
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Скачать CSV",
        data=csv,
        file_name=f"donations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Подвал
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    Дашборд создан для анализа пожертвований фонда<br>
    Данные обновлены: {}
</div>
""".format(datetime.now().strftime('%d.%m.%Y %H:%M')), unsafe_allow_html=True)