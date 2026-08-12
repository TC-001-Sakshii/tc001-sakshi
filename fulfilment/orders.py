from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from .db import get_db
import sqlite3

api = Blueprint("api", __name__)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def serialize_order(db, order_id):
    order = db.execute(
        "SELECT order_id, customer_email, status, created_at FROM orders WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    if order is None:
        return None

    items = db.execute(
        "SELECT sku, quantity FROM order_items WHERE order_id = ? ORDER BY id",
        (order_id,),
    ).fetchall()
    return {
        "order_id": order["order_id"],
        "customer_email": order["customer_email"],
        "status": order["status"],
        "created_at": order["created_at"],
        "items": [dict(item) for item in items],
    }


def is_valid_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/api/orders")
def create_order():
    # Validate JSON is present and is an object
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        return jsonify({"error": "Request body must be valid JSON object"}), 400
    
    order_id = payload.get("order_id")
    customer_email = payload.get("customer_email", "")
    items = payload.get("items", [])

    # Validate order_id
    if not order_id or not isinstance(order_id, str) or order_id.strip() == "":
        return jsonify({"error": "order_id must be a non-empty string"}), 400
    
    # Validate customer_email
    if not customer_email or not isinstance(customer_email, str) or customer_email.strip() == "":
        return jsonify({"error": "customer_email must be a non-empty string"}), 400
    if not is_valid_email(customer_email):
        return jsonify({"error": "customer_email must be a valid email address"}), 400
    
    # Validate items
    if not items or not isinstance(items, list):
        return jsonify({"error": "items must be a non-empty array"}), 400
    
    # Validate each item and check for duplicates
    seen_skus = set()
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "each item must be an object"}), 400
        
        sku = item.get("sku")
        quantity = item.get("quantity")
        
        # Validate sku
        if not sku or not isinstance(sku, str) or sku.strip() == "":
            return jsonify({"error": "item sku must be a non-empty string"}), 400
        
        # Check for duplicate SKUs
        if sku in seen_skus:
            return jsonify({"error": f"duplicate sku in order: {sku}"}), 400
        seen_skus.add(sku)
        
        # Validate quantity - must be positive integer
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            return jsonify({"error": f"item quantity must be a positive integer, got {quantity}"}), 400
        
        # Check SKU exists in inventory
        db = get_db()
        inventory = db.execute(
            "SELECT available_quantity FROM inventory WHERE sku = ?", (sku,)
        ).fetchone()
        if inventory is None:
            return jsonify({"error": f"unknown sku: {sku}"}), 400
    
    # All validations passed - check inventory availability before transaction
    db = get_db()
    
    # Pre-check all inventory levels to avoid partial failures
    for item in items:
        sku = item["sku"]
        quantity = item["quantity"]
        inventory = db.execute(
            "SELECT available_quantity FROM inventory WHERE sku = ?", (sku,)
        ).fetchone()
        
        if inventory["available_quantity"] < quantity:
            return (
                jsonify({"error": "Insufficient inventory", "sku": sku}),
                409,
            )
    
    # All inventory checks passed - execute atomic transaction
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # Insert order
        db.execute(
            "INSERT INTO orders(order_id, customer_email, status, created_at) VALUES (?, ?, ?, ?)",
            (order_id, customer_email, "CREATED", utc_now()),
        )
        
        # Insert all items and update inventory atomically
        for item in items:
            sku = item["sku"]
            quantity = item["quantity"]
            
            db.execute(
                "UPDATE inventory SET available_quantity = available_quantity - ? WHERE sku = ?",
                (quantity, sku),
            )
            db.execute(
                "INSERT INTO order_items(order_id, sku, quantity) VALUES (?, ?, ?)",
                (order_id, sku, quantity),
            )
        
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "Duplicate order ID"}), 409
    except Exception:
        db.rollback()
        raise

    return jsonify({"order": serialize_order(db, order_id)}), 201


@api.get("/api/orders/<order_id>")
def get_order(order_id):
    db = get_db()
    order = serialize_order(db, order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"order": order}), 200


@api.post("/api/orders/<order_id>/events")
def add_event(order_id):
    # Validate JSON is present and is an object
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        return jsonify({"error": "Request body must be valid JSON object"}), 400
    
    event_id = payload.get("event_id")
    new_status = payload.get("status")
    
    # Validate event_id and status are non-empty strings
    if not event_id or not isinstance(event_id, str) or event_id.strip() == "":
        return jsonify({"error": "event_id must be a non-empty string"}), 400
    if not new_status or not isinstance(new_status, str) or new_status.strip() == "":
        return jsonify({"error": "status must be a non-empty string"}), 400
    
    # Validate status is supported
    valid_statuses = {"CREATED", "ALLOCATED", "SHIPPED", "DELIVERED", "CANCELLED"}
    if new_status not in valid_statuses:
        return jsonify({"error": f"unsupported status: {new_status}"}), 400
    
    db = get_db()
    
    order = db.execute(
        "SELECT order_id, status FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    
    current_status = order["status"]
    
    # Check if event_id already exists
    existing_event = db.execute(
        "SELECT event_id, new_status, order_id FROM order_events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    
    if existing_event is not None:
        # Event ID already used
        if existing_event["order_id"] == order_id and existing_event["new_status"] == new_status:
            # Idempotent retry - same event
            return (
                jsonify(
                    {
                        "event_id": event_id,
                        "duplicate": True,
                        "order": serialize_order(db, order_id),
                    }
                ),
                200,
            )
        else:
            # Event ID reused for different order or status
            return jsonify({"error": "Duplicate event_id"}), 409
    
    # Define strict status transitions: CREATED -> ALLOCATED -> SHIPPED -> DELIVERED
    allowed_transitions = {
        "CREATED": {"ALLOCATED", "CANCELLED"},
        "ALLOCATED": {"SHIPPED", "CANCELLED"},
        "SHIPPED": {"DELIVERED"},
        "DELIVERED": set(),
        "CANCELLED": set(),
    }
    
    if new_status not in allowed_transitions.get(current_status, set()):
        return (
            jsonify(
                {
                    "error": "Invalid status transition",
                    "from": current_status,
                    "to": new_status,
                }
            ),
            409,
        )
    
    # Execute entire event operation atomically
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # Insert event
        db.execute(
            "INSERT INTO order_events(event_id, order_id, new_status, created_at) VALUES (?, ?, ?, ?)",
            (event_id, order_id, new_status, utc_now()),
        )
        
        # Update order status
        db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
        
        # Handle inventory restoration for cancellation
        if new_status == "CANCELLED":
            items = db.execute(
                "SELECT sku, quantity FROM order_items WHERE order_id = ?", (order_id,)
            ).fetchall()
            for item in items:
                db.execute(
                    "UPDATE inventory SET available_quantity = available_quantity + ? WHERE sku = ?",
                    (item["quantity"], item["sku"]),
                )
        
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "Duplicate event_id"}), 409
    except Exception:
        db.rollback()
        raise

    return (
        jsonify(
            {
                "event_id": event_id,
                "duplicate": False,
                "order": serialize_order(db, order_id),
            }
        ),
        200,
    )


@api.get("/api/reports/fulfilment")
def fulfilment_report():
    db = get_db()
    report = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM orders) AS total_orders,
            (SELECT COUNT(*) FROM orders WHERE status = 'DELIVERED') AS delivered_orders,
            (SELECT COUNT(*) FROM orders WHERE status = 'CANCELLED') AS cancelled_orders,
            (SELECT COUNT(*) FROM orders WHERE status IN ('CREATED', 'ALLOCATED', 'SHIPPED')) AS pending_orders,
            COALESCE((SELECT SUM(quantity) FROM order_items), 0) AS total_ordered_quantity,
            COALESCE((SELECT SUM(quantity) FROM order_items oi INNER JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'DELIVERED'), 0) AS total_delivered_quantity
        """
    ).fetchone()
    return jsonify({key: report[key] or 0 for key in report.keys()})
