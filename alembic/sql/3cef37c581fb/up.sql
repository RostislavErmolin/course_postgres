-- Остатки товаров на складах
CREATE TABLE inventory.stock (
    warehouse_id INTEGER NOT NULL REFERENCES catalog.warehouses(id),
    product_id   INTEGER NOT NULL REFERENCES catalog.products(id),
    qty          INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0),
    PRIMARY KEY (warehouse_id, product_id)
);

-- Резервы товаров под заказы
-- Привязаны к заказу и товару; склад берётся из orders.warehouse_id
CREATE TABLE inventory.reserves (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES sales.orders(id),
    product_id INTEGER NOT NULL REFERENCES catalog.products(id),
    qty        INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0),
    UNIQUE (order_id, product_id)
);

-- Накладные на доставку заказа покупателю
CREATE TABLE inventory.deliveries (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL UNIQUE REFERENCES sales.orders(id),
    status     VARCHAR NOT NULL DEFAULT 'planned'
               CHECK (status IN ('planned', 'shipping', 'shipped')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    shipped_at TIMESTAMPTZ
);

-- Позиции накладной на доставку (одна строка = один резерв)
CREATE TABLE inventory.delivery_items (
    id          SERIAL PRIMARY KEY,
    delivery_id INTEGER NOT NULL REFERENCES inventory.deliveries(id),
    reserve_id  INTEGER NOT NULL UNIQUE REFERENCES inventory.reserves(id),
    status      VARCHAR NOT NULL DEFAULT 'planned'
                CHECK (status IN ('planned', 'shipped'))
);

-- Накладные на перемещение товаров между складами
CREATE TABLE inventory.transfers (
    id             SERIAL PRIMARY KEY,
    from_city_id   INTEGER NOT NULL,
    to_city_id     INTEGER NOT NULL,
    status         VARCHAR NOT NULL DEFAULT 'planned'
                   CHECK (status IN ('planned', 'shipping', 'in_transit', 'arrived', 'received')),
    total_amount   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at     TIMESTAMPTZ,
    arriving_at    TIMESTAMPTZ,
    received_at    TIMESTAMPTZ,
    FOREIGN KEY (from_city_id, to_city_id)
        REFERENCES inventory.routes(from_city_id, to_city_id)
);

-- Позиции накладной на перемещение
CREATE TABLE inventory.transfer_items (
    id           SERIAL PRIMARY KEY,
    transfer_id  INTEGER NOT NULL REFERENCES inventory.transfers(id),
    product_id   INTEGER NOT NULL REFERENCES catalog.products(id),
    qty          INTEGER NOT NULL CHECK (qty > 0),
    reserve_id   INTEGER REFERENCES inventory.reserves(id),
    requested_by INTEGER NOT NULL REFERENCES auth.users(id),
    status       VARCHAR NOT NULL DEFAULT 'planned'
                 CHECK (status IN ('planned', 'shipped', 'received'))
);
