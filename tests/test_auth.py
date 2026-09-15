import uuid

from app.core.security import hash_password
from app.db.models import User
from conftest import auth_headers_for


def _make_user(db_session, tenant, email="diego@tetecoloh.mx", password="clave-segura-123", role="admin"):
    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
        name="Diego Guzmán",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_with_valid_credentials_returns_token_scoped_to_tenant(client, db_session, tenant):
    _make_user(db_session, tenant)

    response = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "clave-segura-123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == str(tenant.id)
    assert body["role"] == "admin"
    assert body["access_token"]


def test_login_with_wrong_password_is_rejected(client, db_session, tenant):
    _make_user(db_session, tenant)

    response = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "incorrecta"}
    )
    assert response.status_code == 401


def test_login_with_unknown_email_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "no-existe@ejemplo.mx", "password": "cualquiera"}
    )
    assert response.status_code == 401


def test_login_with_inactive_user_is_rejected(client, db_session, tenant):
    user = _make_user(db_session, tenant)
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "clave-segura-123"}
    )
    assert response.status_code == 401


def test_me_returns_the_logged_in_user(client, db_session, tenant):
    user = _make_user(db_session, tenant)

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "clave-segura-123"}
    )
    token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "diego@tetecoloh.mx"
    assert body["role"] == "admin"


def test_me_without_token_is_rejected(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_token_grants_access_to_own_tenant_dashboard(client, db_session, tenant):
    _make_user(db_session, tenant)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "clave-segura-123"}
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        f"/api/v1/dashboard/summary/{tenant.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_login_token_cannot_access_a_different_tenant(client, db_session, tenant):
    _make_user(db_session, tenant)
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "diego@tetecoloh.mx", "password": "clave-segura-123"}
    )
    token = login_resp.json()["access_token"]

    other_tenant_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/dashboard/summary/{other_tenant_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_access_code_verification_issues_a_working_session_token(client, tenant):
    create_resp = client.post(
        "/api/v1/tenants", json={"name": "Restaurante Con Codigo", "slug": f"con-codigo-{uuid.uuid4().hex[:8]}"}
    )
    created = create_resp.json()

    verify_resp = client.post(
        f"/api/v1/tenants/{created['id']}/verify-access", json={"code": created["access_code"]}
    )
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["valid"] is True
    assert body["access_token"]

    dashboard_resp = client.get(
        f"/api/v1/dashboard/summary/{created['id']}",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert dashboard_resp.status_code == 200


def test_access_code_verification_with_wrong_code_has_no_token(client):
    create_resp = client.post(
        "/api/v1/tenants", json={"name": "Restaurante Con Codigo 2", "slug": f"con-codigo2-{uuid.uuid4().hex[:8]}"}
    )
    created = create_resp.json()

    verify_resp = client.post(f"/api/v1/tenants/{created['id']}/verify-access", json={"code": "000000"})
    assert verify_resp.status_code == 200
    body = verify_resp.json()
    assert body["valid"] is False
    assert body["access_token"] is None
