-- catalog_manager: полный доступ к схеме catalog
GRANT USAGE ON SCHEMA catalog TO catalog_manager;
GRANT ALL ON ALL TABLES IN SCHEMA catalog TO catalog_manager;
GRANT ALL ON ALL SEQUENCES IN SCHEMA catalog TO catalog_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON TABLES TO catalog_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT ALL ON SEQUENCES TO catalog_manager;

-- sales_manager: полный доступ к схеме sales
GRANT USAGE ON SCHEMA sales TO sales_manager;
GRANT ALL ON ALL TABLES IN SCHEMA sales TO sales_manager;
GRANT ALL ON ALL SEQUENCES IN SCHEMA sales TO sales_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    GRANT ALL ON TABLES TO sales_manager;
ALTER DEFAULT PRIVILEGES IN SCHEMA sales
    GRANT ALL ON SEQUENCES TO sales_manager;

-- Все роли имеют доступ на чтение catalog (текущие и будущие объекты)
GRANT USAGE ON SCHEMA catalog TO catalog_manager, sales_manager;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO sales_manager;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT SELECT ON TABLES TO sales_manager;
