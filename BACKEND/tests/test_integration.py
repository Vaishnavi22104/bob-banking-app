"""
test_integration.py — Integration tests for the full request/response cycle.

Uses Flask's test client to send real HTTP requests through the full
stack (routing → business logic → database) without a network connection.
All tests run against an in-memory SQLite database via the fixtures in
conftest.py.
"""


# ---------------------------------------------------------------------------
# Helper: log the test client in as the seeded customer
# ---------------------------------------------------------------------------

def _login(client, username="testuser", password="correctpassword"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestLogin:
    def test_get_login_returns_200(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"Sign In" in resp.data or b"Login" in resp.data

    def test_correct_credentials_redirect_to_dashboard(self, client, seeded_customer):
        resp = _login(client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_wrong_password_stays_on_login(self, client, seeded_customer):
        resp = client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid credentials" in resp.data

    def test_unknown_username_stays_on_login(self, client, clean_db):
        resp = client.post(
            "/login",
            data={"username": "nobody", "password": "anything"},
            follow_redirects=True,
        )
        assert b"Invalid credentials" in resp.data

    def test_empty_fields_rejected(self, client):
        resp = client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_already_logged_in_redirected_from_login(self, client, seeded_customer):
        _login(client)
        resp = client.get("/login", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]


class TestLogout:
    def test_logout_clears_session_and_redirects(self, client, seeded_customer):
        _login(client)
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_dashboard_inaccessible_after_logout(self, client, seeded_customer):
        _login(client)
        client.get("/logout")
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Session guard
# ---------------------------------------------------------------------------


class TestSessionGuard:
    def test_dashboard_redirects_when_not_logged_in(self, client):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_deposit_redirects_when_not_logged_in(self, client):
        resp = client.post("/deposit", data={"amount": "50"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_withdraw_redirects_when_not_logged_in(self, client):
        resp = client.post("/withdraw", data={"amount": "50"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_dashboard_shows_balance_after_login(self, client, seeded_customer):
        _login(client)
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"500.00" in resp.data

    def test_dashboard_shows_customer_name(self, client, seeded_customer):
        _login(client)
        resp = client.get("/dashboard")
        assert b"Test User" in resp.data


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------


class TestDepositRoute:
    def test_valid_deposit_redirects_to_dashboard(self, client, seeded_customer):
        _login(client)
        resp = client.post("/deposit", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_deposit_updates_balance_on_dashboard(self, client, seeded_customer):
        _login(client)
        client.post("/deposit", data={"amount": "200"})
        resp = client.get("/dashboard")
        assert b"700.00" in resp.data

    def test_zero_deposit_shows_error(self, client, seeded_customer):
        _login(client)
        resp = client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data.lower()

    def test_non_numeric_deposit_shows_error(self, client, seeded_customer):
        _login(client)
        resp = client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        assert b"valid number" in resp.data.lower()


# ---------------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------------


class TestWithdrawRoute:
    def test_valid_withdrawal_redirects_to_dashboard(self, client, seeded_customer):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_withdrawal_updates_balance_on_dashboard(self, client, seeded_customer):
        _login(client)
        client.post("/withdraw", data={"amount": "150"})
        resp = client.get("/dashboard")
        assert b"350.00" in resp.data

    def test_overdraft_shows_insufficient_funds_message(self, client, seeded_customer):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "9999"}, follow_redirects=True)
        assert b"insufficient" in resp.data.lower()

    def test_zero_withdrawal_shows_error(self, client, seeded_customer):
        _login(client)
        resp = client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data.lower()


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------


class TestErrorPages:
    def test_404_returns_correct_status(self, client):
        resp = client.get("/this-route-does-not-exist")
        assert resp.status_code == 404
