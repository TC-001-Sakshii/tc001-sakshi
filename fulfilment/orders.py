from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from .db import get_db


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

    db = get_db()
    db.execute(
        "INSERT INTO orders(order_id, customer_email, status, created_at) VALUES (?, ?, ?, ?)",
        (order_id, customer_email, "CREATED", utc_now()),
    )
    db.commit()

    for item in items:
        sku = item["sku"]
        quantity = int(item["quantity"])
        inventory = db.execute(
            "SELECT available_quantity FROM inventory WHERE sku = ?", (sku,)
        ).fetchone()

        if inventory is None or inventory["available_quantity"] <= quantity:
            return (
                jsonify({"error": "Insufficient inventory", "sku": sku}),
                409,
            )

        db.execute(
            "UPDATE inventory SET available_quantity = available_quantity - ? WHERE sku = ?",
            (quantity, sku),
        )
        db.execute(
            "INSERT INTO order_items(order_id, sku, quantity) VALUES (?, ?, ?)",
            (order_id, sku, quantity),
        )
        db.commit()

    return jsonify({"order": serialize_order(db, order_id)}), 201


@api.get("/api/orders/<order_id>")
def get_order(order_id):
    db = get_db()
    return jsonify({"order": serialize_order(db, order_id)}), 200


@api.post("/api/orders/<order_id>/events")
def add_event(order_id):
    payload = request.get_json(silent=True) or {}
    event_id = payload.get("event_id")
    new_status = payload.get("status")
    db = get_db()

    order = db.execute(
        "SELECT order_id, status FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    allowed_transitions = {
        "CREATED": {"ALLOCATED", "SHIPPED", "CANCELLED"},
        "ALLOCATED": {"SHIPPED", "CANCELLED"},
        "SHIPPED": {"DELIVERED", "CANCELLED"},
        "DELIVERED": set(),
        "CANCELLED": set(),
    }

    if new_status not in allowed_transitions.get(order["status"], set()):
        return (
            jsonify(
                {
                    "error": "Invalid status transition",
                    "from": order["status"],
                    "to": new_status,
                }
            ),
            409,
        )

    db.execute(
        "INSERT INTO order_events(event_id, order_id, new_status, created_at) VALUES (?, ?, ?, ?)",
        (event_id, order_id, new_status, utc_now()),
    )
    db.commit()

    db.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    db.commit()

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
            COUNT(o.order_id) AS total_orders,
            SUM(CASE WHEN o.status = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered_orders,
            SUM(CASE WHEN o.status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_orders,
            SUM(CASE WHEN o.status IN ('CREATED', 'ALLOCATED', 'SHIPPED') THEN 1 ELSE 0 END) AS pending_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_ordered_quantity,
            COALESCE(SUM(CASE WHEN o.status = 'DELIVERED' THEN oi.quantity ELSE 0 END), 0) AS total_delivered_quantity
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        LEFT JOIN order_events oe ON oe.order_id = o.order_id
        """
    ).fetchone()
    return jsonify({key: report[key] or 0 for key in report.keys()})
