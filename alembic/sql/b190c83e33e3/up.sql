CREATE TABLE inventory.routes (
    from_city_id INTEGER NOT NULL REFERENCES catalog.cities(id),
    to_city_id   INTEGER NOT NULL REFERENCES catalog.cities(id),
    duration     INTERVAL NOT NULL,
    total_threshold NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (from_city_id, to_city_id),
    CONSTRAINT routes_different_cities CHECK (from_city_id <> to_city_id)
);
