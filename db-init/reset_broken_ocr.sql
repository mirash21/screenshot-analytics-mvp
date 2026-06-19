-- Сброс скриншотов, ошибочно помеченных unknown из-за сбоя OCR (2026-06-10)
-- OCR падал с "No closing quotation" из-за битого tessedit_char_whitelist

WITH broken AS (
    SELECT screenshot_id
    FROM analysis_results
    WHERE category = 'unknown'
      AND (ocr_text IS NULL OR TRIM(ocr_text) = '')
      AND analyzed_at >= '2026-06-10 08:23:00'
)
DELETE FROM analysis_results
WHERE screenshot_id IN (SELECT screenshot_id FROM broken);

UPDATE screenshots
SET status = 'pending'
WHERE status = 'analyzed'
  AND id NOT IN (SELECT screenshot_id FROM analysis_results);
