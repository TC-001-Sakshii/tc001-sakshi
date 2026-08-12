import pytest


def make_order(order_id, sku="SKU-MOUSE", quantity=1):
    return {
        "order_id": order_id,
        "customer_email": f"{order_id.lower()}@example.com",
        "items": [{"sku": sku, "quantity": quantity}],
    }


def test_created_order_contains_expected_details(client):
    response = client.post(
        "/api/orders",
        json=make_order("ORD-EXTRA-1", "SKU-KEYBOARD", 2),
    )

    assert response.status_code == 201

    order = response.get_json()["order"]
    assert order["order_id"] == "ORD-EXTRA-1"
    assert order["customer_email"] == "ord-extra-1@example.com"
    assert order["status"] == "CREATED"
    assert order["items"][0]["sku"] == "SKU-KEYBOARD"
    assert order["items"][0]["quantity"] == 2


def test_order_rejects_quantity_above_available_stock(client):
    response = client.post(
        "/api/orders",
        json=make_order("ORD-EXTRA-2", "SKU-HEADSET", 4),
    )

    assert response.status_code == 409
    assert response.is_json
    assert "error" in response.get_json()


def test_unknown_event_status_is_rejected(client):
    client.post(
        "/api/orders",
        json=make_order("ORD-EXTRA-3"),
    )

    response = client.post(
        "/api/orders/ORD-EXTRA-3/events",
        json={
            "event_id": "EXTRA-EVENT-1",
            "status": "PROCESSING",
        },
    )

    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.get_json()


def test_allocating_order_updates_its_status(client):
    client.post(
        "/api/orders",
        json=make_order("ORD-EXTRA-4"),
    )

    response = client.post(
        "/api/orders/ORD-EXTRA-4/events",
        json={
            "event_id": "EXTRA-EVENT-2",
            "status": "ALLOCATED",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["order"]["status"] == "ALLOCATED"


def test_report_counts_single_created_order(client):
    client.post(
        "/api/orders",
        json=make_order("ORD-EXTRA-5", "SKU-MOUSE", 2),
    )

    response = client.get("/api/reports/fulfilment")

    assert response.status_code == 200
    assert response.get_json() == {
        "total_orders": 1,
        "delivered_orders": 0,
        "cancelled_orders": 0,
        "pending_orders": 1,
        "total_ordered_quantity": 2,
        "total_delivered_quantity": 0,
    }
