-- Отзываем права inventory_manager на sales
ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    REVOKE SELECT ON TABLES FROM inventory_manager;
REVOKE UPDATE (status) ON sales.orders FROM inventory_manager;
REVOKE SELECT ON ALL TABLES IN SCHEMA sales FROM inventory_manager;
REVOKE USAGE ON SCHEMA sales FROM inventory_manager;

-- Отзываем права inventory_manager на catalog
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    REVOKE SELECT ON TABLES FROM inventory_manager;
REVOKE SELECT ON ALL TABLES IN SCHEMA catalog FROM inventory_manager;
REVOKE USAGE ON SCHEMA catalog FROM inventory_manager;

-- Отзываем права inventory_manager на inventory
ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    REVOKE ALL ON SEQUENCES FROM inventory_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    REVOKE ALL ON TABLES FROM inventory_manager;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA inventory FROM inventory_manager;
REVOKE ALL ON ALL TABLES IN SCHEMA inventory FROM inventory_manager;
REVOKE USAGE ON SCHEMA inventory FROM inventory_manager;
