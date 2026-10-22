from .conftest import login


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ai_active"] is False
    assert r.json()["db"] == "ok"


def test_bad_login(client):
    r = client.post("/api/auth/login", data={"username": "priya.sharma@email.com", "password": "nope"})
    assert r.status_code == 401


def test_no_token(client):
    assert client.get("/api/me/books").status_code == 401


def test_roles_are_separated(client, author_h, admin_h):
    assert client.get("/api/admin/tickets", headers=author_h).status_code == 403
    assert client.get("/api/me/tickets", headers=admin_h).status_code == 403


def test_author_sees_only_own_books(client, author_h):
    books = client.get("/api/me/books", headers=author_h).json()
    assert len(books) > 0
    other = login(client, "rohit.kapoor@email.com", "author123")
    other_books = client.get("/api/me/books", headers=other).json()
    assert {b["id"] for b in books}.isdisjoint({b["id"] for b in other_books})


def test_cannot_raise_ticket_on_someone_elses_book(client, author_h):
    other = login(client, "rohit.kapoor@email.com", "author123")
    foreign = client.get("/api/me/books", headers=other).json()[0]["id"]
    r = client.post("/api/me/tickets", headers=author_h,
                    json={"book_id": foreign, "subject": "hello", "description": "not my book"})
    assert r.status_code == 400


def test_validation_error_is_422(client, author_h):
    r = client.post("/api/me/tickets", headers=author_h, json={"subject": "a", "description": "b"})
    assert r.status_code == 422


def test_ticket_flow_with_fallback_triage(client, author_h, admin_h):
    book = client.get("/api/me/books", headers=author_h).json()[0]
    r = client.post("/api/me/tickets", headers=author_h, json={
        "book_id": book["id"],
        "subject": "Royalty not received",
        "description": "I still haven't received my royalty payment after 6 months.",
    })
    assert r.status_code == 201
    tid = r.json()["id"]
    # no key in tests, so this is the keyword fallback
    assert r.json()["category"] == "Royalty & Payments"
    assert r.json()["priority"] == "Critical"

    # admin: draft, note, override, reply
    d = client.post(f"/api/admin/tickets/{tid}/ai-draft", headers=admin_h).json()
    assert d["source"] == "fallback" and d["draft"]

    r = client.post(f"/api/admin/tickets/{tid}/notes", headers=admin_h, json={"body": "check with finance"})
    assert r.status_code == 201

    r = client.patch(f"/api/admin/tickets/{tid}/priority", headers=admin_h, json={"priority": "Low"})
    body = r.json()
    assert body["priority"] == "Low" and body["ai_priority"] == "Critical" and body["priority_overridden"] == 1

    r = client.post(f"/api/admin/tickets/{tid}/responses", headers=admin_h,
                    json={"body": "We are on it.", "was_ai_drafted": False})
    assert r.status_code == 201
    assert r.json()["status"] == "In Progress"

    # author sees the reply but nothing internal
    mine = client.get(f"/api/me/tickets/{tid}", headers=author_h).json()
    assert len(mine["responses"]) == 1
    assert "notes" not in mine and "ai_category" not in mine


def test_other_author_cannot_open_ticket(client, author_h):
    tid = client.get("/api/me/tickets", headers=author_h).json()[0]["id"]
    other = login(client, "rohit.kapoor@email.com", "author123")
    assert client.get(f"/api/me/tickets/{tid}", headers=other).status_code == 404


def test_login_sets_httponly_cookie_and_cookie_works(client):
    r = client.post("/api/auth/login", data={"username": "priya.sharma@email.com", "password": "author123"})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "bl_session=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    # the TestClient keeps the cookie, so this call has no Authorization header
    assert client.get("/api/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/me").status_code == 401


def test_login_is_rate_limited(client):
    for _ in range(5):
        r = client.post("/api/auth/login", data={"username": "ananya.reddy@email.com", "password": "wrong"})
        assert r.status_code == 401
    r = client.post("/api/auth/login", data={"username": "ananya.reddy@email.com", "password": "author123"})
    assert r.status_code == 429 and "retry-after" in r.headers
    # a different account is not affected
    r = client.post("/api/auth/login", data={"username": "rohit.kapoor@email.com", "password": "author123"})
    assert r.status_code == 200
