DROP TABLE IF EXISTS catalog.products;
DROP TABLE IF EXISTS catalog.product_categories;
DROP TABLE IF EXISTS catalog.warehouses;
DROP SCHEMA IF EXISTS catalog;

CREATE SCHEMA catalog;
GRANT ALL ON SCHEMA catalog TO app_user;

CREATE TABLE catalog.product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL
);

CREATE TABLE catalog.products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES catalog.product_categories(id)
);

CREATE TABLE catalog.warehouses (
    id SERIAL PRIMARY KEY,
    city VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    label VARCHAR,
    is_central BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX one_central_warehouse ON catalog.warehouses (is_central)
WHERE is_central = TRUE;

GRANT ALL ON ALL TABLES IN SCHEMA catalog TO app_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA catalog TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON SEQUENCES TO app_user;
