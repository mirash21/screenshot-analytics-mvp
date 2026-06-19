FROM python:3.11-slim

# Установка Tesseract OCR и русских языковых данных
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка EasyOCR (альтернативный нейросетевой OCR)
RUN pip install --no-cache-dir easyocr

# Копирование кода
COPY . .

# Создание директорий для логов
RUN mkdir -p /app/storage

# Переменная окружения для выбора OCR движка
# TESSERACT или EASYOCR
ENV OCR_ENGINE=TESSERACT

CMD ["python", "analyzer.py"]
