# TC Fulfilment API

Flask/SQLite API for managing customer orders, inventory, fulfilment events, and reporting.

## Features

- Create and retrieve orders
- Reserve inventory during order creation
- Process fulfilment events
- Handle cancellation and inventory restoration
- Enforce valid status transitions
- Generate fulfilment reports
- Validate API input and database data
- Run locally and deploy with Gunicorn/Render

## Quick Start

### Local Setup (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python app.py
```

The server runs at `http://localhost:5000`.

### Run Tests

```powershell
pytest -q tests/
```


## API

### Health Check

```http
GET /health
```

Returns:

```json
{"status": "ok"}
```

### Create Order

```http
POST /api/orders
Content-Type: application/json

{
  "order_id": "ORD-1001",
  "customer_email": "customer@example.com",
  "items": [
    {"sku": "SKU-KEYBOARD", "quantity": 2},
    {"sku": "SKU-MOUSE", "quantity": 1}
  ]
}
```

Successful creation returns HTTP 201.

Common errors:
- `400` - Invalid request data
- `409` - Duplicate order ID or insufficient inventory

### Get Order

```http
GET /api/orders/ORD-1001
```

Returns HTTP 200 for an existing order and HTTP 404 if the order is not found.

### Process Event

```http
POST /api/orders/ORD-1001/events
Content-Type: application/json

{
  "event_id": "EVT-1001-A",
  "status": "ALLOCATED"
}
```

Normal status flow:

```text
CREATED -> ALLOCATED -> SHIPPED -> DELIVERED
```

Cancellation is allowed from `CREATED` or `ALLOCATED`. Inventory is restored as part of the same transaction.

A repeated event with the same `event_id`, order, and status is treated as a duplicate.

### Fulfilment Report

```http
GET /api/reports/fulfilment
```

Example response:

```json
{
  "total_orders": 10,
  "delivered_orders": 3,
  "cancelled_orders": 2,
  "pending_orders": 5,
  "total_ordered_quantity": 45,
  "total_delivered_quantity": 12
}
```

## Database

### Tables

**Orders**
- `order_id` - primary key
- `customer_email`
- `status`
- `created_at`

**Inventory**
- `sku` - primary key
- `available_quantity`

**Order Items**
- `id` - primary key
- `order_id` - foreign key
- `sku` - foreign key
- `quantity`
- `(order_id, sku)` is unique

**Order Events**
- `id` - primary key
- `event_id` - unique
- `order_id` - foreign key
- `new_status`
- `created_at`

### Initial Stock

| SKU | Quantity |
|---|---:|
| SKU-KEYBOARD | 5 |
| SKU-MOUSE | 10 |
| SKU-HEADSET | 3 |

SQLite foreign key enforcement is enabled and the schema includes checks for valid statuses and quantities.

## Testing

The project includes the supplied smoke tests and evaluator tests.

Main areas covered:
- Input validation
- Inventory handling
- Transaction rollback
- Status transitions
- Event idempotency
- Cancellation
- Report calculations
- Database constraints

```powershell
pytest -q tests/
```

## Defects Fixed

The 14 issues addressed in the starter project were:

1. JSON validation
2. Order input validation
3. Duplicate order IDs
4. Exact stock handling
5. Atomic order creation
6. Foreign key enforcement
7. Missing order response
8. Status transition validation
9. Event validation
10. Event idempotency
11. Atomic event processing
12. Cancellation handling
13. Report count calculation
14. Render start command

See `DEFECT_REPORT.md` for the individual issues and fixes.

## Deployment

The application can be deployed to Render using Gunicorn.

### Render Configuration

- Runtime: Python 3
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variable: `PYTHONUNBUFFERED=1`

After deployment, verify:

```text
https://<your-service>.onrender.com/health
```

## Documentation

- `PROBLEM_STATEMENT.md` - Requirements and business rules
- `DEFECT_REPORT.md` - Defects and fixes
- `AI_USAGE.md` - AI usage notes
- `schema.sql` - Database schema
- `seed.sql` - Initial data

## Error Responses

Errors use JSON with an appropriate HTTP status:

```json
{
  "error": "Descriptive error message"
}
```

Status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request
- `404` - Not found
- `409` - Conflict

## Technology Stack

- Python
- Flask
- SQLite
- Pytest
- Gunicorn
- Render
