-- inventory_manager: полный доступ к схеме inventory
GRANT USAGE ON SCHEMA inventory TO inventory_manager;
GRANT ALL ON ALL TABLES IN SCHEMA inventory TO inventory_manager;
GRANT ALL ON ALL SEQUENCES IN SCHEMA inventory TO inventory_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    GRANT ALL ON TABLES TO inventory_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    GRANT ALL ON SEQUENCES TO inventory_manager;

-- inventory_manager: чтение схемы catalog
GRANT USAGE ON SCHEMA catalog TO inventory_manager;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO inventory_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT SELECT ON TABLES TO inventory_manager;

-- inventory_manager: чтение схемы sales + обновление статуса заказа
GRANT USAGE ON SCHEMA sales TO inventory_manager;
GRANT SELECT ON ALL TABLES IN SCHEMA sales TO inventory_manager;
GRANT UPDATE (status) ON sales.orders TO inventory_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    GRANT SELECT ON TABLES TO inventory_manager;
