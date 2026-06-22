-- psql -h 127.0.0.1 -p 5433 -U postgres -f setup.sql

CREATE DATABASE inventorydb;
CREATE USER app_user WITH PASSWORD 'example';
GRANT ALL PRIVILEGES ON DATABASE inventorydb TO app_user;

-- Роли приложения (без пароля — вход только через app_user)
CREATE ROLE catalog_manager;
CREATE ROLE sales_manager;
CREATE ROLE inventory_manager;
CREATE ROLE worker;
CREATE ROLE supervisor IN ROLE catalog_manager, sales_manager;

\c inventorydb

-- Права на схему public
GRANT CREATE ON SCHEMA public TO app_user;

-- Расширение для хеширования паролей
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Схема авторизации (управляется суперпользователем вне миграций)
CREATE SCHEMA auth;

CREATE TABLE auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    password VARCHAR NOT NULL,
    role VARCHAR NOT NULL CHECK (
        role IN ('catalog_manager', 'sales_manager', 'inventory_manager', 'worker')
    )
);

-- Доступ app_user к auth.users
GRANT USAGE ON SCHEMA auth TO app_user;
GRANT SELECT ON auth.users TO app_user;
GRANT REFERENCES ON auth.users TO app_user;

-- Тестовые пользователи
INSERT INTO auth.users (username, password, role) VALUES
    ('cat_man',  crypt('catalog123',   gen_salt('bf')), 'catalog_manager'),
    ('sales_man',crypt('sales123',     gen_salt('bf')), 'sales_manager'),
    ('inv_man',  crypt('inventory123', gen_salt('bf')), 'inventory_manager'),
    ('worker1',  crypt('worker123',    gen_salt('bf')), 'worker');
