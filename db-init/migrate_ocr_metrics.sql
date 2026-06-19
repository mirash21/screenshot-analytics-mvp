-- Миграция технических OCR-метрик для существующих PostgreSQL баз.
-- Используется для баз, созданных до добавления колонок ocr_engine, ocr_duration_ms и ocr_metrics.

ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS ocr_engine VARCHAR(50);
ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS ocr_duration_ms INTEGER;
ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS ocr_metrics JSONB;
