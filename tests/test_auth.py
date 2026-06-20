def test_register_returns_201(client):
    response = client.post("/auth/register", json={"username": "adi", "password": "secret"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "adi"
    assert data["role"] == "user"
    assert "id" in data
    assert "password" not in data


def test_register_duplicate_returns_409(client):
    payload = {"username": "adi", "password": "secret"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"]


def test_login_returns_token(client):
    client.post("/auth/register", json={"username": "adi", "password": "secret"})
    response = client.post("/token", data={"username": "adi", "password": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"username": "adi", "password": "secret"})
    response = client.post("/token", data={"username": "adi", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_unknown_user_returns_401(client):
    response = client.post("/token", data={"username": "nobody", "password": "secret"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_me_returns_current_user(client):
    client.post("/auth/register", json={"username": "adi", "password": "secret"})
    token = client.post("/token", data={"username": "adi", "password": "secret"}).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "adi"
    assert data["role"] == "user"
    assert "id" in data


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401


# ── Admin route ──


def test_admin_users_with_admin_token_returns_200(client, test_db):
    from app.auth import hash_password

    # Register endpoint only creates 'user' role, so seed admin directly.
    test_db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
        ("adminuser", hash_password("adminpass")),
    )
    test_db.commit()

    token = client.post("/token", data={"username": "adminuser", "password": "adminpass"}).json()[
        "access_token"
    ]
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    users = response.json()
    assert any(u["username"] == "adminuser" for u in users)


def test_admin_users_with_regular_token_returns_403(client):
    client.post("/auth/register", json={"username": "adi", "password": "secret"})
    token = client.post("/token", data={"username": "adi", "password": "secret"}).json()[
        "access_token"
    ]
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_users_without_token_returns_401(client):
    response = client.get("/admin/users")
    assert response.status_code == 401


# ── Change password ──


def test_change_password_success(auth_client):
    response = auth_client.post(
        "/auth/change-password",
        json={"current_password": "testpass", "new_password": "newpass123"},
    )
    assert response.status_code == 204

    # Can now log in with the new password
    login = auth_client.post("/token", data={"username": "testuser", "password": "newpass123"})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_change_password_wrong_current_password(auth_client):
    response = auth_client.post(
        "/auth/change-password",
        json={"current_password": "wrongpass", "new_password": "newpass123"},
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"]


def test_change_password_unauthenticated(client):
    response = client.post(
        "/auth/change-password",
        json={"current_password": "testpass", "new_password": "newpass123"},
    )
    assert response.status_code == 401
