# ИСПОЛЬЗУЕМ ОФИЦИАЛЬНЫЙ СТАБИЛЬНЫЙ ОБРАЗ PYTHON
FROM python:3.12-slim

# НАСТРОЙКА ОКРУЖЕНИЯ PYTHON
# Вывод логов напрямую в консоль без буферизации
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# УСТАНОВКА СИСТЕМНЫХ ЗАВИСИМОСТЕЙ ДЛЯ СБОРКИ И ПОДКЛЮЧЕНИЯ К POSTGRESQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# СОЗДАНИЕ РАБОЧЕЙ ДИРЕКТОРИИ ВНУТРИ КОНТЕЙНЕРА
WORKDIR /app

# УСТАНОВКА ЗАВИСИМОСТЕЙ PYTHON
COPY src/requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# КОПИРОВАНИЕ ИСХОДНОГО КОДА ПРОЕКТА
COPY src/ /app/src/
