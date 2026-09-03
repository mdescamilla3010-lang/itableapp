import uuid


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_tenant_and_duplicate_slug_conflict(client):
    payload = {"name": "Restaurante API", "slug": "restaurante-api-test"}
    r1 = client.post("/api/v1/tenants", json=payload)
    assert r1.status_code == 201
    tenant_id = r1.json()["id"]

    r2 = client.post("/api/v1/tenants", json=payload)
    assert r2.status_code == 409

    r3 = client.get(f"/api/v1/tenants/{tenant_id}")
    assert r3.status_code == 200
    assert r3.json()["slug"] == "restaurante-api-test"


def test_get_missing_tenant_returns_404(client):
    response = client.get(f"/api/v1/tenants/{uuid.uuid4()}")
    assert response.status_code == 404


def test_sync_for_missing_tenant_returns_404(client):
    response = client.post(f"/api/v1/sync/{uuid.uuid4()}", json={"orders": []})
    assert response.status_code == 404


def test_dashboard_for_missing_tenant_returns_404(client):
    response = client.get(f"/api/v1/dashboard/summary/{uuid.uuid4()}")
    assert response.status_code == 404


def test_sync_and_dashboard_flow(client):
    tenant_resp = client.post(
        "/api/v1/tenants", json={"name": "Restaurante Sync", "slug": "restaurante-sync-test"}
    )
    tenant_id = tenant_resp.json()["id"]

    payload = {
        "orders": [
            {
                "external_order_id": "ORD-API-1",
                "staff_external_id": "W-API-1",
                "staff_name": "Pedro Ramirez",
                "total_amount": "300.00",
                "discount_amount": "0",
                "status": "COMPLETED",
                "order_date": "2026-01-01T12:00:00Z",
                "items": [
                    {
                        "external_product_id": "PA-1",
                        "product_name": "Torta",
                        "quantity": 3,
                        "unit_price": "100.00",
                        "unit_cost": "40.00",
                    }
                ],
            }
        ]
    }
    sync_resp = client.post(f"/api/v1/sync/{tenant_id}", json=payload)
    assert sync_resp.status_code == 201
    assert sync_resp.json()["orders_created"] == 1

    dedup_resp = client.post(f"/api/v1/sync/{tenant_id}", json=payload)
    assert dedup_resp.json()["orders_skipped_duplicate"] == 1

    dashboard_resp = client.get(f"/api/v1/dashboard/summary/{tenant_id}")
    assert dashboard_resp.status_code == 200
    assert dashboard_resp.json()["total_sales"] == "300.00"

    staff_audit_resp = client.get(f"/api/v1/analytics/staff-audit/{tenant_id}")
    assert staff_audit_resp.status_code == 200

    menu_resp = client.get(f"/api/v1/analytics/menu-engineering/{tenant_id}")
    assert menu_resp.status_code == 200
    assert menu_resp.json()["items"][0]["product_name"] == "Torta"

    cash_resp = client.get(f"/api/v1/analytics/cash-audit/{tenant_id}")
    assert cash_resp.status_code == 200


def test_cash_shift_sync_and_audit_flow(client):
    tenant_resp = client.post(
        "/api/v1/tenants", json={"name": "Restaurante Caja", "slug": "restaurante-caja-test"}
    )
    tenant_id = tenant_resp.json()["id"]

    payload = {
        "shifts": [
            {
                "external_shift_id": "SH-API-1",
                "staff_external_id": "C-API-1",
                "staff_name": "Luis Cajero",
                "expected_cash": "1000.00",
                "actual_cash": "950.00",
                "shift_start": "2026-01-01T08:00:00Z",
                "shift_end": "2026-01-01T16:00:00Z",
            }
        ]
    }
    sync_resp = client.post(f"/api/v1/sync/{tenant_id}/cash-shifts", json=payload)
    assert sync_resp.status_code == 201
    assert sync_resp.json() == {
        "shifts_received": 1,
        "shifts_created": 1,
        "shifts_skipped_duplicate": 0,
        "staff_created": 1,
    }

    dedup_resp = client.post(f"/api/v1/sync/{tenant_id}/cash-shifts", json=payload)
    assert dedup_resp.json()["shifts_skipped_duplicate"] == 1

    cash_resp = client.get(f"/api/v1/analytics/cash-audit/{tenant_id}")
    assert cash_resp.status_code == 200
    body = cash_resp.json()
    assert body["total_accumulated_discrepancy"] == "-50.00"
    assert body["cashiers"][0]["staff_name"] == "Luis Cajero"


def test_cash_shift_sync_for_missing_tenant_returns_404(client):
    response = client.post(f"/api/v1/sync/{uuid.uuid4()}/cash-shifts", json={"shifts": []})
    assert response.status_code == 404
