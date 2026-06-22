-- Отзываем права worker на catalog
ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    REVOKE SELECT ON TABLES FROM worker;
REVOKE SELECT ON ALL TABLES IN SCHEMA catalog FROM worker;
REVOKE USAGE ON SCHEMA catalog FROM worker;

-- Отзываем права worker на inventory
REVOKE UPDATE (status) ON inventory.transfer_items FROM worker;
REVOKE UPDATE (status, started_at, arriving_at, received_at) ON inventory.transfers FROM worker;
REVOKE UPDATE (status) ON inventory.delivery_items FROM worker;
REVOKE UPDATE (status, shipped_at) ON inventory.deliveries FROM worker;
REVOKE UPDATE (qty) ON inventory.reserves FROM worker;
REVOKE ALL ON inventory.stock FROM worker;

ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    REVOKE SELECT ON TABLES FROM worker;
REVOKE SELECT ON ALL TABLES IN SCHEMA inventory FROM worker;
REVOKE USAGE ON SCHEMA inventory FROM worker;
