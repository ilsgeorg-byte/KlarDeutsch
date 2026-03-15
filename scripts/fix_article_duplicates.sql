-- Исправление дублирования артикля у слова Wohnung
-- Запустить в вашей базе данных

-- Найти проблемные записи
SELECT id, article, de, ru 
FROM words 
WHERE de ILIKE '%Wohnung%' 
   OR article LIKE '%% %'  -- Артикль содержит пробел (дублируется)
   OR article LIKE 'die die%'
   OR article LIKE 'der der%'
   OR article LIKE 'das das%';

-- Исправить (заменить "die die" на "die")
UPDATE words 
SET article = TRIM(REPLACE(article, 'die die', 'die'))
WHERE article LIKE '%die die%';

-- Исправить (заменить "der der" на "der")
UPDATE words 
SET article = TRIM(REPLACE(article, 'der der', 'der'))
WHERE article LIKE '%der der%';

-- Исправить (заменить "das das" на "das")
UPDATE words 
SET article = TRIM(REPLACE(article, 'das das', 'das'))
WHERE article LIKE '%das das%';

-- Проверить результат
SELECT id, article, de, ru 
FROM words 
WHERE de ILIKE '%Wohnung%';
