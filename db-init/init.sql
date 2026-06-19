-- Инициализация базы данных PostgreSQL для системы анализа скриншотов

-- Таблица сотрудников
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица скриншотов
CREATE TABLE IF NOT EXISTS screenshots (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    capture_time TIME NOT NULL,
    capture_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица результатов анализа
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    screenshot_id INTEGER NOT NULL UNIQUE REFERENCES screenshots(id) ON DELETE CASCADE,
    ocr_text TEXT,
    category VARCHAR(20) NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    details TEXT,
    ocr_engine VARCHAR(50),
    ocr_duration_ms INTEGER,
    ocr_metrics JSONB,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ключевых слов
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL CHECK(category IN ('work', 'user', 'productive', 'unproductive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_screenshots_date ON screenshots(capture_date);
CREATE INDEX IF NOT EXISTS idx_screenshots_employee ON screenshots(employee_id, capture_date);
CREATE INDEX IF NOT EXISTS idx_analysis_category ON analysis_results(category);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
