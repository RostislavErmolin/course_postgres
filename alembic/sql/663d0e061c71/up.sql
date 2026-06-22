-- worker: чтение схемы inventory
GRANT USAGE ON SCHEMA inventory TO worker;
GRANT SELECT ON ALL TABLES IN SCHEMA inventory TO worker;

ALTER DEFAULT PRIVILEGES IN SCHEMA inventory
    GRANT SELECT ON TABLES TO worker;

-- worker: чтение схемы catalog (нужно видеть товары и склады)
GRANT USAGE ON SCHEMA catalog TO worker;
GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO worker;

ALTER DEFAULT PRIVILEGES IN SCHEMA catalog
    GRANT SELECT ON TABLES TO worker;

-- worker: полные права на stock (приёмка/отгрузка меняет остатки)
GRANT ALL ON inventory.stock TO worker;

-- worker: обновление количества в резервах (при приёмке с перемещения)
GRANT UPDATE (qty) ON inventory.reserves TO worker;

-- worker: обновление статуса и даты отгрузки накладной доставки
GRANT UPDATE (status, shipped_at) ON inventory.deliveries TO worker;

-- worker: обновление статуса позиций накладной доставки
GRANT UPDATE (status) ON inventory.delivery_items TO worker;

-- worker: обновление статуса и дат накладной перемещения
GRANT UPDATE (status, started_at, arriving_at, received_at) ON inventory.transfers TO worker;

-- worker: обновление статуса позиций накладной перемещения
GRANT UPDATE (status) ON inventory.transfer_items TO worker;
