-- Добавляем как nullable, чтобы не нарушить существующие строки
ALTER TABLE sales.orders ADD COLUMN created_by INTEGER REFERENCES auth.users(id);

-- Заполняем существующие строки первым доступным пользователем
UPDATE sales.orders SET created_by = (SELECT id FROM auth.users ORDER BY id LIMIT 1)
WHERE created_by IS NULL;

-- Теперь можно сделать NOT NULL
ALTER TABLE sales.orders ALTER COLUMN created_by SET NOT NULL;
