# Руководство по настройке EasyOCR

## 📋 Обзор

Система поддерживает два OCR движка:
- **Tesseract** - классический движок (быстрее, меньше RAM)
- **EasyOCR** - нейросетевой движок (лучше качество для русского языка и сложных интерфейсов)

## 🚀 Быстрый старт с EasyOCR

### Шаг 1: Настройка .env файла

Откройте `.env` файл и измените следующие параметры:

```env
# Переключение на EasyOCR
OCR_ENGINE=EASYOCR

# Минимальный confidence для текста (0.0-1.0)
# Рекомендуемые значения:
#   0.3 - по умолчанию (баланс полноты/точности)
#   0.5 - более строгий фильтр
#   0.7 - только высококачественное распознавание
EASYOCR_MIN_CONFIDENCE=0.3
```

### Шаг 2: Перезапуск контейнера

```powershell
# Пересборка и перезапуск
docker-compose up -d --build ocr-analyzer

# Или просто перезапуск (если образ уже собран)
docker-compose restart ocr-analyzer
```

### Шаг 3: Проверка работы

```powershell
# Просмотр логов
docker-compose logs -f ocr-analyzer
```

Вы должны увидеть сообщения вида:
```
EasyOCR инициализирован (CPU mode)
EasyOCR статистика: 15 блоков, avg_conf=0.82, min=0.45, max=0.98, >=0.7: 12
```

## 🔬 A/B Тестирование движков

Для сравнения качества Tesseract и EasyOCR используйте встроенный скрипт:

### Способ 1: Через временный Docker-контейнер

Скрипт находится в корне проекта, поэтому его удобно подключать в контейнер через volume:

```powershell
# Запуск теста на 10 скриншотах
docker run --rm -v "${PWD}\storage:/app/storage" -v "${PWD}\scripts\test_ocr_engines.py:/app/scripts/test_ocr_engines.py" mvp-ocr-analyzer bash -c "TEST_LIMIT=10 python /app/scripts/test_ocr_engines.py"

# Запуск теста на 50 скриншотах
docker run --rm -v "${PWD}\storage:/app/storage" -v "${PWD}\scripts\test_ocr_engines.py:/app/scripts/test_ocr_engines.py" mvp-ocr-analyzer bash -c "TEST_LIMIT=50 python /app/scripts/test_ocr_engines.py"
```

Альтернативно можно скопировать скрипт в уже запущенный контейнер и выполнить через `docker exec`:

```powershell
docker cp scripts/test_ocr_engines.py screenshot-analyzer:/app/scripts/test_ocr_engines.py
docker exec screenshot-analyzer bash -c "TEST_LIMIT=10 python /app/scripts/test_ocr_engines.py"
```

### Способ 2: Локально (требует установки зависимостей)

```powershell
cd scripts
python test_ocr_engines.py
```

### Анализ результатов

Скрипт выведет:
- Среднее время обработки каждого движка
- Среднюю длину распознанного текста
- Средний OCR confidence
- Quality score с учетом длины текста, confidence и скорости
- Соотношение качества и скорости
- Рекомендацию по выбору движка

Пример вывода:
```
ИТОГОВАЯ СТАТИСТИКА
====================

Среднее время обработки:
  Tesseract: 4.23 сек
  EasyOCR:   6.87 сек
  Соотношение: 0.62x

Средняя длина текста:
  Tesseract: 245 символов
  EasyOCR:   312 символов
  Tesseract avg_conf: 0.41
  EasyOCR avg_conf: 0.78
  Tesseract avg_score: 18.4
  EasyOCR avg_score: 35.1
  Соотношение: 1.27x

🏆 РЕКОМЕНДАЦИЯ: Использовать EasyOCR (лучшее качество)
```

## ⚙️ Параметры настройки

### OCR_ENGINE

Выбор OCR движка:
- `TESSERACT` - использовать Tesseract (по умолчанию)
- `EASYOCR` - использовать EasyOCR

### EASYOCR_MIN_CONFIDENCE

Минимальный порог уверенности для включения текста в результат:
- `0.0-0.3` - максимальная полнота (может включать ошибки)
- `0.3-0.5` - баланс (рекомендуется)
- `0.5-0.7` - высокая точность
- `0.7-1.0` - только очень уверенные результаты

### OCR_CACHE_ENABLED / OCR_CACHE_TTL_SECONDS / OCR_CACHE_MAX_ITEMS

OCR-результаты кэшируются по хешу файла, mtime, размеру, OCR-движку и confidence threshold.
Это ускоряет повторную обработку одного и того же скриншота и снижает нагрузку на OCR.

- `OCR_CACHE_ENABLED=true` - включить кэш по умолчанию
- `OCR_CACHE_TTL_SECONDS=86400` - срок жизни записи, 1 день
- `OCR_CACHE_MAX_ITEMS=1000` - максимум записей в JSON-кэше
- `OCR_CACHE_FILE=/app/storage/ocr_cache.json` - файл кэша

Для честного A/B-теста кэш автоматически отключается в [`scripts/test_ocr_engines.py`](scripts/test_ocr_engines.py:1).

### Примеры конфигураций

**Для максимальной точности:**
```env
OCR_ENGINE=EASYOCR
EASYOCR_MIN_CONFIDENCE=0.7
OCR_CACHE_ENABLED=true
OCR_CACHE_TTL_SECONDS=86400
OCR_CACHE_MAX_ITEMS=1000
OCR_CACHE_FILE=/app/storage/ocr_cache.json
```

**Для баланса скорость/качество:**
```env
OCR_ENGINE=EASYOCR
EASYOCR_MIN_CONFIDENCE=0.5
OCR_CACHE_ENABLED=true
OCR_CACHE_TTL_SECONDS=86400
OCR_CACHE_MAX_ITEMS=1000
OCR_CACHE_FILE=/app/storage/ocr_cache.json
```

**Для максимальной полноты:**
```env
OCR_ENGINE=EASYOCR
EASYOCR_MIN_CONFIDENCE=0.3
OCR_CACHE_ENABLED=true
OCR_CACHE_TTL_SECONDS=86400
OCR_CACHE_MAX_ITEMS=1000
OCR_CACHE_FILE=/app/storage/ocr_cache.json
```

## 📊 Мониторинг качества

### Просмотр статистики confidence

В логах analyzer можно видеть статистику по каждому скриншоту:

```powershell
docker-compose logs ocr-analyzer | Select-String "EasyOCR статистика"
```

Пример:
```
EasyOCR статистика: 18 блоков, avg_conf=0.79, min=0.42, max=0.97, >=0.7: 14
```

Это означает:
- Распознано 18 текстовых блоков
- Средняя уверенность: 79%
- Минимальная: 42%
- Максимальная: 97%
- 14 блоков имеют уверенность >= 70%

Также в логах появляются общие метрики через `OCR metrics`: длина текста, токены, confidence, duration, image type, PSM и quality flags.

### Сравнение в БД

Можно сравнить результаты в базе данных:

```sql
-- Средняя длина OCR текста
SELECT 
    AVG(LENGTH(ocr_text)) as avg_text_length,
    COUNT(*) as total_analyzed
FROM analysis_results;

-- Распределение по категориям
SELECT 
    category,
    COUNT(*) as count,
    ROUND(AVG(confidence), 2) as avg_confidence
FROM analysis_results
GROUP BY category;
```

## 💡 Рекомендации по выбору движка

### Используйте EasyOCR если:
- ✅ Много русских текстов
- ✅ Сложные интерфейсы (SAP, 1C)
- ✅ Нестандартные шрифты
- ✅ Качество важнее скорости
- ✅ Есть запас RAM (2GB+)

### Используйте Tesseract если:
- ✅ Нужна максимальная скорость
- ✅ Ограниченная память (<2GB)
- ✅ Простые документы/таблицы
- ✅ Стандартные шрифты
- ✅ Большой объем скриншотов (>2000/день)

## 🔧 Оптимизация производительности

### Для EasyOCR:

1. **Увеличить лимит памяти** в docker-compose.yml:
```yaml
ocr-analyzer:
  deploy:
    resources:
      limits:
        memory: 3G  # вместо 2G
```

2. **Уменьшить batch size**:
```env
BATCH_SIZE=5  # вместо 10
```

3. **Настроить confidence threshold**:
```env
EASYOCR_MIN_CONFIDENCE=0.5  # фильтровать слабые результаты
```

### Для Tesseract:

1. **Оптимизировать PSM режимы** (уже настроено автоматически)

2. **Увеличить batch size**:
```env
BATCH_SIZE=15
```

## 🐛 Troubleshooting

### EasyOCR не запускается

```powershell
# Проверка логов
docker-compose logs ocr-analyzer | Select-String "EasyOCR"

# Если ошибка импорта - пересобрать образ
docker-compose build --no-cache ocr-analyzer
docker-compose up -d ocr-analyzer
```

### Слишком медленная обработка

```powershell
# Уменьшить batch size
# В .env:
BATCH_SIZE=5

# Или переключиться на Tesseract
OCR_ENGINE=TESSERACT
```

### Плохое качество распознавания

Попробуйте разные пороги confidence:
```env
EASYOCR_MIN_CONFIDENCE=0.5  # или 0.7 для строгого фильтра
```

Проверьте логи на предмет low confidence:
```powershell
docker-compose logs ocr-analyzer | Select-String "min="
```

## 📈 Сравнительная таблица

| Параметр | Tesseract | EasyOCR |
|----------|-----------|---------|
| Скорость | ⚡⚡⚡⚡ | ⚡⚡ |
| Качество (русский) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Качество (интерфейсы) | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Потребление RAM | ~500MB | ~1.5-2GB |
| Confidence scores | heuristic | ✅ |
| Настройка сложности | Средняя | Простая |
| Fallback механизм | N/A | → Tesseract |

## 🎯 Заключение

Рекомендуемый подход:
1. **Запустить A/B тест** на реальных скриншотах
2. **Проанализировать результаты** (качество vs скорость)
3. **Выбрать оптимальный движок** под ваши задачи
4. **Настроить confidence threshold** для фильтрации шума
5. **Мониторить качество** через логи и метрики БД
6. **Смотреть JSON-отчет** `/app/storage/ocr_comparison.json`

Для большинства случаев с русским языком и сложными интерфейсами **EasyOCR показывает лучшие результаты**, несмотря на меньшую скорость обработки.
