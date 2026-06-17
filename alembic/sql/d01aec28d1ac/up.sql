CREATE SCHEMA sales;
GRANT ALL ON SCHEMA sales TO app_user;

CREATE TABLE sales.orders (
    id SERIAL PRIMARY KEY,
    status VARCHAR NOT NULL DEFAULT 'unpublished'
        CHECK (status IN ('unpublished', 'new', 'processing', 'pending', 'packing', 'shipped')),
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    warehouse_id INTEGER NOT NULL REFERENCES catalog.warehouses(id)
);

CREATE TABLE sales.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES sales.orders(id),
    product_id INTEGER NOT NULL REFERENCES catalog.products(id),
    price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

GRANT ALL ON ALL TABLES IN SCHEMA sales TO app_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA sales TO app_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    GRANT ALL ON SEQUENCES TO app_user;
