# Миграция на PostgreSQL

## Что изменилось

Система была обновлена для использования **PostgreSQL** вместо SQLite. Это обеспечивает:

- ✅ Лучшую производительность при concurrent access
- ✅ Поддержку большего количества пользователей
- ✅ Надежность и отказоустойчивость
- ✅ Возможность горизонтального масштабирования
- ✅ Продвинутые возможности БД (транзакции, блокировки, etc.)

## Основные изменения

### 1. Docker Compose

Добавлен сервис PostgreSQL:
```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: screenshot_analytics
    POSTGRES_USER: ${DB_USER:-admin}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./db-init/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
```

### 2. Переменные окружения

В `.env` файле добавлены новые параметры:
```env
DB_USER=admin
DB_PASSWORD=ваш_пароль
DB_HOST=postgres
DB_PORT=5432
DB_NAME=screenshot_analytics
```

### 3. Код модулей

Все модули (`data-collector`, `ocr-analyzer`, `dashboard`) теперь используют `psycopg2` для работы с PostgreSQL.

SQL запросы изменены с SQLite синтаксиса (`?`) на PostgreSQL (`%s`).

### 4. SQL схема

Обновлена для PostgreSQL:
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `TEXT` → `VARCHAR(255)` где применимо
- `REAL` → `FLOAT`
- `FOREIGN KEY` → inline `REFERENCES`
- Добавлен `ON CONFLICT ... DO UPDATE` вместо `INSERT OR REPLACE`

## Развертывание с PostgreSQL

### Шаг 1: Настройка .env файла

```powershell
copy .env.example .env
notepad .env
```

Установите надежный пароль для PostgreSQL:
```env
DB_USER=admin
DB_PASSWORD=SuperSecurePassword123!
```

### Шаг 2: Запуск системы

```powershell
docker-compose up -d
```

PostgreSQL автоматически:
1. Создаст базу данных `screenshot_analytics`
2. Выполнит `init.sql` для создания таблиц
3. Будет доступен для других сервисов

### Шаг 3: Проверка

```powershell
# Проверка статуса всех сервисов
docker-compose ps

# Логи PostgreSQL
docker-compose logs postgres

# Подключение к БД для проверки
docker exec -it screenshot-postgres psql -U admin -d screenshot_analytics
```

Внутри psql:
```sql
-- Проверка таблиц
\dt

-- Проверка данных
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM screenshots;
SELECT COUNT(*) FROM keywords;
```

## Миграция данных из SQLite (если нужно)

Если у вас уже есть данные в SQLite и вы хотите перенести их в PostgreSQL:

### Шаг 1: Экспорт из SQLite

```python
import sqlite3
import csv

# Подключение к SQLite
sqlite_conn = sqlite3.connect('analytics.db')
sqlite_cursor = sqlite_conn.cursor()

# Экспорт каждой таблицы в CSV
tables = ['employees', 'screenshots', 'analysis_results', 'keywords']

for table in tables:
    sqlite_cursor.execute(f"SELECT * FROM {table}")
    rows = sqlite_cursor.fetchall()
    
    with open(f'{table}.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in sqlite_cursor.description])
        writer.writerows(rows)

sqlite_conn.close()
print("Экспорт завершен")
```

### Шаг 2: Импорт в PostgreSQL

```python
import psycopg2
import csv

# Подключение к PostgreSQL
pg_conn = psycopg2.connect(
    host='localhost',
    database='screenshot_analytics',
    user='admin',
    password='your_password'
)
pg_cursor = pg_conn.cursor()

# Импорт каждой таблицы
tables = ['employees', 'screenshots', 'analysis_results', 'keywords']

for table in tables:
    with open(f'{table}.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Создание запроса INSERT
        placeholders = ', '.join(['%s'] * len(headers))
        columns = ', '.join(headers)
        
        for row in reader:
            pg_cursor.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                row
            )

pg_conn.commit()
pg_conn.close()
print("Импорт завершен")
```

## Миграция OCR-метрик

Для существующих баз выполните миграцию технических колонок OCR-метрик:

```powershell
docker exec -i screenshot-postgres psql -U admin -d screenshot_analytics < db-init/migrate_ocr_metrics.sql
```

Миграция добавляет в `analysis_results`:

- `ocr_engine` — использованный OCR-движок;
- `ocr_duration_ms` — время OCR-распознавания;
- `ocr_metrics` — JSON-метрики качества.

## Преимущества PostgreSQL

### Производительность
- **Concurrent reads/writes**: Несколько процессов могут работать с БД одновременно
- **Better indexing**: Продвинутые типы индексов (B-tree, Hash, GiST, GIN)
- **Query optimization**: Автоматическая оптимизация запросов

### Масштабируемость
- **Horizontal scaling**: Возможность репликации и шардинга
- **Connection pooling**: PgBouncer для управления подключениями
- **Partitioning**: Разделение больших таблиц по датам

### Надежность
- **ACID compliance**: Полная поддержка транзакций
- **WAL (Write-Ahead Logging)**: Защита от потери данных
- **Point-in-time recovery**: Восстановление на любой момент времени

### Функциональность
- **Full-text search**: Встроенный полнотекстовый поиск
- **JSON/JSONB**: Поддержка JSON данных
- **Arrays**: Массивы в колонках
- **Custom types**: Пользовательские типы данных

## Мониторинг PostgreSQL

### Проверка состояния

```powershell
# Статистика подключений
docker exec -it screenshot-postgres psql -U admin -d screenshot_analytics -c "SELECT count(*) FROM pg_stat_activity;"

# Размер базы данных
docker exec -it screenshot-postgres psql -U admin -d screenshot_analytics -c "SELECT pg_size_pretty(pg_database_size('screenshot_analytics'));"

# Топ медленных запросов
docker exec -it screenshot-postgres psql -U admin -d screenshot_analytics -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Бэкап базы данных

```powershell
# Создание бэкапа
docker exec screenshot-postgres pg_dump -U admin screenshot_analytics > backup_$(Get-Date -Format 'yyyyMMdd').sql

# Восстановление из бэкапа
cat backup_20260603.sql | docker exec -i screenshot-postgres psql -U admin screenshot_analytics
```

### Автоматический бэкап (Task Scheduler)

Создайте задачу в Windows Task Scheduler:

**Действие:** PowerShell.exe  
**Аргументы:**
```powershell
-Command "docker exec screenshot-postgres pg_dump -U admin screenshot_analytics | Out-File -FilePath 'C:\Backup\screenshot_db_$(Get-Date -Format yyyyMMdd_HHmmss).sql'"
```

**Расписание:** Ежедневно в 2:00 AM

## Troubleshooting

### PostgreSQL не запускается

```powershell
# Проверка логов
docker-compose logs postgres

# Проверка volume
docker volume ls | grep postgres
```

### Ошибка подключения

```powershell
# Проверка что сервис запущен
docker-compose ps postgres

# Проверка переменных окружения
docker-compose config | Select-String "DB_"
```

### Медленные запросы

```sql
-- Включение pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Анализ медленных запросов
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Очистка старых данных

```sql
-- Удаление скриншотов старше 30 дней
DELETE FROM screenshots WHERE capture_date < CURRENT_DATE - INTERVAL '30 days';

-- Очистка пустых сотрудников
DELETE FROM employees e WHERE NOT EXISTS (
    SELECT 1 FROM screenshots s WHERE s.employee_id = e.id
);

-- Vacuum для освобождения места
VACUUM FULL;
```

## Сравнение: SQLite vs PostgreSQL

| Характеристика | SQLite | PostgreSQL |
|---|---|---|
| Concurrent writes | ❌ Нет | ✅ Да |
| Max DB size | ~140 TB | Unlimited |
| Users | 1 | Unlimited |
| Replication | ❌ Нет | ✅ Да |
| Backup online | ❌ Нет | ✅ Да |
| Full-text search | Базовый | Продвинутый |
| JSON support | Limited | Full (JSONB) |
| Memory usage | Низкое | Среднее |
| Setup complexity | Простой | Средний |

## Заключение

Переход на PostgreSQL обеспечивает систему надежной, масштабируемой базой данных, готовой к росту нагрузки и количества пользователей. Все данные защищены WAL журналированием и поддерживают полноценные транзакции.

Для MVP на 25 сотрудников это избыточно, но закладывает фундамент для будущего масштабирования.
