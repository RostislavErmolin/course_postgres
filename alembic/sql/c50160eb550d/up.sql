CREATE TABLE catalog.cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE
);

INSERT INTO catalog.cities (name) VALUES
    ('Москва'),
    ('Санкт-Петербург'),
    ('Новосибирск'),
    ('Екатеринбург'),
    ('Казань'),
    ('Нижний Новгород'),
    ('Челябинск'),
    ('Самара'),
    ('Омск'),
    ('Ростов-на-Дону'),
    ('Уфа'),
    ('Красноярск'),
    ('Воронеж'),
    ('Пермь'),
    ('Волгоград');

GRANT ALL ON catalog.cities TO app_user;
GRANT ALL ON catalog.cities_id_seq TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON SEQUENCES TO app_user;

ALTER TABLE catalog.warehouses ADD COLUMN city_id INTEGER REFERENCES catalog.cities(id);

UPDATE catalog.warehouses w
SET city_id = c.id
FROM catalog.cities c
WHERE c.name = w.city;

ALTER TABLE catalog.warehouses ALTER COLUMN city_id SET NOT NULL;

ALTER TABLE catalog.warehouses DROP COLUMN city;
