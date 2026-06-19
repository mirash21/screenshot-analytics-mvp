-- Миграция: добавление колонки details в analysis_results
-- Запуск для существующей БД:
-- docker exec -i screenshot-postgres psql -U admin -d screenshot_analytics < db-init/migrate_add_details.sql

ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS details TEXT;

-- Обновление старых категорий на новые (work/user)
UPDATE analysis_results SET category = 'work' WHERE category = 'productive';
UPDATE analysis_results SET category = 'user' WHERE category = 'unproductive';
