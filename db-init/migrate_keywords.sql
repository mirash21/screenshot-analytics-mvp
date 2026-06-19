,
-- Миграция: обновление категорий keywords с productive/unproductive на work/user
-- Запускается один раз при обновлении до версии 2.0.0

-- Обновляем категории
UPDATE keywords SET category = 'work' WHERE category = 'productive';
UPDATE keywords SET category = 'user' WHERE category = 'unproductive';

-- Обновляем constraint если нужно (в новой версии init.sql уже обновлен)
-- ALTER TABLE keywords DROP CONSTRAINT IF EXISTS keywords_category_check;
-- ALTER TABLE keywords ADD CONSTRAINT keywords_category_check CHECK(category IN ('work', 'user', 'productive', 'unproductive'));

-- Удаляем старые категории если остались
DELETE FROM keywords WHERE category IN ('productive', 'unproductive');
