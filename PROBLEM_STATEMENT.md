# Technical Hands-on Assessment

**Role:** Engineering Support Intern — Python, AI, Automation and QA  
**Date:** Wednesday, 12 August 2026  
**Assessment window:** 3:00 PM–6:00 PM IST  
**Duration:** 3 hours  
**Difficulty:** Hard  
**Technology:** Python, Flask, SQLite, REST/JSON, Pytest, Git and Render

## Objective

You have received an existing order-fulfilment API. The service accepts customer orders, reserves inventory, processes fulfilment events, and produces a summary report. The current code runs, but it contains functional, validation, database, transaction, idempotency, reporting, and deployment defects.

Diagnose and correct the application. Do not rebuild it in another programming language or replace the API with a different framework. Reasonable refactoring within the existing Python/Flask structure is allowed.

## Required API behaviour

All error responses must be JSON and use an appropriate HTTP status code. A consistent error format is expected.

### 1. Health check

`GET /health`

- Return HTTP `200` when the service is running.

### 2. Create an order

`POST /api/orders`

Example request:

```json
{
  "order_id": "ORD-1001",
  "customer_email": "customer@example.com",
  "items": [
    {"sku": "SKU-KEYBOARD", "quantity": 2},
    {"sku": "SKU-MOUSE", "quantity": 1}
  ]
}
```

Required behaviour:

- `order_id` must be a non-empty string and unique.
- `customer_email` must be a non-empty, plausibly valid email address.
- `items` must be a non-empty array.
- Every item must contain a valid, existing `sku` and a positive integer `quantity`. Boolean, decimal, numeric-string, zero, and negative quantities are invalid.
- A SKU may appear only once in one order.
- Exact available stock is sufficient and must be accepted.
- The complete order must be atomic. If any item fails, no order, order item, or inventory change may remain.
- Successful creation returns HTTP `201` with the created order in `CREATED` status.
- Duplicate order IDs and insufficient inventory return HTTP `409`.
- Malformed JSON and invalid input return HTTP `400`.

### 3. Retrieve an order

`GET /api/orders/{order_id}`

- Return the order and its items with HTTP `200`.
- Return HTTP `404` when the order does not exist.

### 4. Process an order event

`POST /api/orders/{order_id}/events`

Example request:

```json
{
  "event_id": "EVT-1001-A",
  "status": "ALLOCATED"
}
```

Required status flow:

```text
CREATED -> ALLOCATED -> SHIPPED -> DELIVERED
```

Cancellation rules:

- `CANCELLED` is allowed only from `CREATED` or `ALLOCATED`.
- Cancellation restores all inventory reserved for the order exactly once.
- No transition is allowed from `DELIVERED` or `CANCELLED`.

Event requirements:

- `event_id` and `status` are required non-empty strings.
- Skipping a status is invalid; for example, `CREATED -> SHIPPED` must fail.
- A repeated `event_id` with the same order and status is an idempotent retry: return HTTP `200`, set `duplicate` to `true`, and do not repeat any side effect.
- Reusing an `event_id` for a different order or status returns HTTP `409`.
- An invalid transition returns HTTP `409`.
- An unknown order returns HTTP `404`.
- Event insertion, status update, and inventory restoration must be one database transaction.

### 5. Fulfilment report

`GET /api/reports/fulfilment`

Return HTTP `200` with these integer fields:

```json
{
  "total_orders": 0,
  "delivered_orders": 0,
  "cancelled_orders": 0,
  "pending_orders": 0,
  "total_ordered_quantity": 0,
  "total_delivered_quantity": 0
}
```

Definitions:

- Pending orders have status `CREATED`, `ALLOCATED`, or `SHIPPED`.
- `total_ordered_quantity` includes quantities from all successfully created orders, including later-cancelled orders.
- `total_delivered_quantity` includes quantities only from orders currently in `DELIVERED` status.
- Joins or multiple events must not cause an order or quantity to be counted more than once.

## Automated tests

Add at least **10 meaningful Pytest tests**. Your tests must cover both positive and negative cases, including:

- successful multi-item creation;
- duplicate-order rejection;
- exact-stock acceptance;
- malformed and invalid input;
- insufficient-inventory rollback;
- unknown-order retrieval;
- invalid and valid status transitions;
- duplicate-event idempotency and event-ID conflict;
- cancellation and one-time inventory restoration;
- cancellation after shipment rejection;
- report accuracy after orders have different statuses.

The three supplied smoke tests are not counted as your complete test suite.

## Deployment

Deploy the corrected application as a **Render Free web service**.

- The application must start successfully and `/health` must be accessible.
- Dependencies and the production start command must be correct.
- Use environment variables for configuration.
- Do not commit passwords, tokens, API keys, or other secrets.
- SQLite data may reset when the free service restarts; seeded demonstration data is acceptable for this assessment.

Use the prefix `TC_001_<name>` for the GitHub repository and Render service. If you were instructed to create separate assessment accounts, use the same prefix wherever the platform permits. **Never submit or share account passwords.**

## Submission

Submit all of the following by **6:00 PM IST**:

1. GitHub repository URL containing the corrected code and commit history.
2. Working Render `onrender.com` URL.
3. Automated tests.
4. Updated `README.md` with setup, test, API, and deployment instructions.
5. `DEFECT_REPORT.md` listing each defect found, its root cause, the fix, and the test that proves the fix.
6. `AI_USAGE.md` stating which AI tools were used, representative prompts or assistance received, and how the generated suggestions were verified.

## AI-tool policy

ChatGPT and other AI tools are permitted. You remain responsible for every submitted line, correctness, security, and test coverage. A short live review may follow. You may be asked to explain a transaction, debug a failing test, or make a small change without advance notice.

## Evaluation

| Area | Marks |
|---|---:|
| Functional correctness and business rules | 20 |
| Database integrity and transactions | 15 |
| API validation and error handling | 10 |
| State transitions and idempotency | 10 |
| Report correctness | 10 |
| Automated test quality and coverage | 15 |
| Code quality, configuration and security | 10 |
| Git history, documentation and Render deployment | 10 |
| **Total** | **100** |

The recommended shortlist score is **75 or above**, subject to satisfactory explanation during the live technical review.
