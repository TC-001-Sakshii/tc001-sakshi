# Defect Report - TC Fulfilment API

## Overview

The starter application contained several deliberate issues in input handling, order processing, inventory, events, reporting, and deployment. Related issues were grouped together below to keep the report focused.

## Defect #1: Request and Order Validation

**Area:** Input Handling and Validation  
**Severity:** High

### Issue
Order creation did not properly validate malformed JSON, required fields, email format, SKU values, quantities, or duplicate SKUs.

### Fix
Added request and field validation before database operations:
- Valid JSON object required
- Required order fields checked
- Customer email format checked
- SKUs checked against inventory
- Quantities must be positive integers
- Duplicate SKUs in one order are rejected

### Verification
Invalid request data returns HTTP 400.

## Defect #2: Order and Inventory Transaction Handling

**Area:** Order Processing and Inventory  
**Severity:** Critical

### Issue
Order creation could leave partial changes in the database if one item failed. There was also an issue with accepting an order when the requested quantity exactly matched available stock.

### Fix
Order creation was moved into a single transaction so the order, order items, and inventory changes are committed together.

The stock check was also changed from:

```python
if inventory["available_quantity"] <= quantity:
```

to:

```python
if inventory["available_quantity"] < quantity:
```

### Verification
- Exact available stock is accepted.
- Insufficient stock returns HTTP 409.
- A failure during a multi-item order rolls back the complete operation.

## Defect #3: Duplicate Order Handling

**Area:** Order Management  
**Severity:** High

### Issue
A duplicate `order_id` caused an unhandled SQLite `IntegrityError` and returned HTTP 500.

### Fix
Handled the integrity error, rolled back the transaction, and returned HTTP 409.

### Verification
A duplicate order ID returns 409 and does not deduct inventory a second time.

## Defect #4: Database Integrity and Constraints

**Area:** Database  
**Severity:** High

### Issue
SQLite foreign key enforcement was disabled and some invalid values could be stored without database-level checks.

### Fix
Enabled foreign keys and added constraints for:
- Valid order status values
- Positive quantities
- Non-negative inventory
- Unique event IDs
- Unique `(order_id, sku)` pairs

### Verification
Invalid database values are rejected and foreign key enforcement is enabled.

## Defect #5: Order Status and Cancellation Rules

**Area:** Order State Management  
**Severity:** High

### Issue
Invalid status transitions were allowed, including:

```text
CREATED -> SHIPPED
SHIPPED -> CANCELLED
```

Cancellation could also restore inventory more than once.

### Fix
Enforced the allowed order flow:

```text
CREATED -> ALLOCATED -> SHIPPED -> DELIVERED
```

Cancellation is allowed only from `CREATED` or `ALLOCATED`. Inventory restoration is handled inside the cancellation transaction.

### Verification
- Invalid transitions return HTTP 409.
- Cancellation after shipment is rejected.
- Repeating a cancellation does not restore inventory twice.

## Defect #6: Order Retrieval and Event Validation

**Area:** API Validation and Responses  
**Severity:** Medium

### Issue
Two related API validation issues were present:
- A missing order returned HTTP 200 with a null value.
- Event requests did not validate `event_id` and `status`.

### Fix
Missing orders now return HTTP 404. Event requests require a non-empty event ID and a supported status.

### Verification
- Missing order -> 404
- Missing or invalid event fields -> 400

## Defect #7: Event Idempotency

**Area:** Event Processing  
**Severity:** High

### Issue
The same event could be processed more than once because `event_id` was not enforced as unique.

### Fix
Added a unique constraint and checked existing events before processing.

If the same event is retried with the same order and status, the API returns `duplicate: true`. Reusing the ID for different data returns HTTP 409.

### Verification
Tested new events, repeated events, and conflicting event IDs.

## Defect #8: Event Transaction Atomicity

**Area:** Event Processing  
**Severity:** Critical

### Issue
Event insertion, order status updates, and inventory restoration used separate commits. A failure in the middle could leave the database in an inconsistent state.

### Fix
Wrapped the complete event operation in one transaction:

```python
db.execute("BEGIN IMMEDIATE")
# insert event
# update order status
# restore inventory when required
db.commit()
```

### Verification
Event processing either completes all related changes or rolls them back.

## Defect #9: Fulfilment Report Calculation

**Area:** Reporting  
**Severity:** High

### Issue
The report joined orders, order items, and events together. Multiple items and events for the same order multiplied rows and produced incorrect counts.

For example, 2 items and 3 events could result in 6 joined rows for one order.

### Fix
Changed the report calculations to use independent subqueries for the individual counts and quantity totals.

### Verification
Report totals were checked with orders containing multiple items and events and matched the expected values.

## Defect #10: Render Deployment Configuration

**Area:** Deployment  
**Severity:** High

### Issue
`render.yaml` referenced a WSGI object named `application`:

```yaml
startCommand: gunicorn app:application
```

The Flask object in the application is named `app`.

### Fix

```yaml
startCommand: gunicorn app:app
```

### Verification
The service starts successfully and `/health` returns HTTP 200.

## Summary

| # | Category | Severity | Status |
|---|---|---|---|
| 1 | Request and Order Validation | High | Fixed |
| 2 | Order and Inventory Transactions | Critical | Fixed |
| 3 | Duplicate Orders | High | Fixed |
| 4 | Database Integrity | High | Fixed |
| 5 | Status and Cancellation | High | Fixed |
| 6 | Retrieval and Event Validation | Medium | Fixed |
| 7 | Event Idempotency | High | Fixed |
| 8 | Event Atomicity | Critical | Fixed |
| 9 | Reporting | High | Fixed |
| 10 | Deployment | High | Fixed |

All 10 grouped defects were addressed and the available evaluator tests pass.
