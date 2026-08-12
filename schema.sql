CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_email TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CREATED', 'ALLOCATED', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    sku TEXT PRIMARY KEY,
    available_quantity INTEGER NOT NULL CHECK (available_quantity >= 0)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sku) REFERENCES inventory(sku),
    UNIQUE(order_id, sku)
);

CREATE TABLE IF NOT EXISTS order_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    order_id TEXT NOT NULL,
    new_status TEXT NOT NULL CHECK (new_status IN ('CREATED', 'ALLOCATED', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
