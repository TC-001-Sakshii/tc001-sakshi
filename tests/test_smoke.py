def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_basic_order(client):
    response = client.post(
        "/api/orders",
        json={
            "order_id": "ORD-SMOKE-1",
            "customer_email": "smoke@example.com",
            "items": [{"sku": "SKU-MOUSE", "quantity": 1}],
        },
    )
    assert response.status_code == 201
    assert response.get_json()["order"]["status"] == "CREATED"


def test_get_existing_order(client):
    client.post(
        "/api/orders",
        json={
            "order_id": "ORD-SMOKE-2",
            "customer_email": "reader@example.com",
            "items": [{"sku": "SKU-KEYBOARD", "quantity": 1}],
        },
    )
    response = client.get("/api/orders/ORD-SMOKE-2")
    assert response.status_code == 200
    assert response.get_json()["order"]["order_id"] == "ORD-SMOKE-2"
