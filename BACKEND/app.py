"""
app.py — Flask application entry point for the Banking Web Application.

Responsibilities
----------------
1. Create and configure the Flask app instance.
2. Initialise Flask-SQLAlchemy against the local SQLite database.
3. Register all route handlers (auth, dashboard, transactions).
4. Register custom HTTP error handlers (404, 500).
5. Create database tables on first start (idempotent).

Run
---
    python app.py          # development server on http://127.0.0.1:5000
"""

import os
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import verify_password
from models import Customer, db
from transactions import deposit as svc_deposit
from transactions import withdraw as svc_withdraw

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "FRONTEND")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)

# --- Configuration ----------------------------------------------------------
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'banking.db')}",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- Initialise extensions --------------------------------------------------
db.init_app(app)

# ---------------------------------------------------------------------------
# Route-protection decorator
# ---------------------------------------------------------------------------


def login_required(f):
    """
    Decorator that redirects to /login if no valid session exists.
    Apply to every route that requires authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "customer_id" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    """Redirect root URL to /login or /dashboard depending on session state."""
    if "customer_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  — render the login form.
         If already authenticated, redirect straight to /dashboard.
    POST — validate credentials; on success store customer_id in session
         and redirect to /dashboard; on failure flash a generic error.
    """
    # Already logged in — skip the login page.
    if "customer_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Server-side: both fields are required.
        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        customer = Customer.query.filter_by(username=username).first()

        # Use the same generic message whether the username or password
        # is wrong — prevents username enumeration.
        if customer is None or not verify_password(customer.password_hash, password):
            flash("Invalid credentials. Please try again.", "error")
            return render_template("login.html")

        # Credentials are valid — establish the session.
        session.clear()
        session["customer_id"] = customer.id
        session["customer_name"] = customer.full_name
        return redirect(url_for("dashboard"))

    # GET — just render the form.
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear the session and redirect to the login page."""
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard route
# ---------------------------------------------------------------------------


@app.route("/dashboard")
@login_required
def dashboard():
    """
    Display the customer's current balance.
    Balance is always read fresh from the database — never from the session.
    """
    customer = db.session.get(Customer, session["customer_id"])
    if customer is None:
        # Edge case: customer was deleted from the DB while session was live.
        session.clear()
        flash("Account not found. Please log in again.", "error")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        customer_name=customer.full_name,
        balance=customer.balance,
    )


# ---------------------------------------------------------------------------
# Transaction routes  (POST-only; always redirect → Post/Redirect/Get)
# ---------------------------------------------------------------------------


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    """
    Accept a deposit amount, delegate to the service layer, flash the result,
    and redirect back to /dashboard (Post/Redirect/Get pattern).
    """
    raw_amount = request.form.get("amount", "")
    success, message = svc_deposit(session["customer_id"], raw_amount)
    flash(message, "success" if success else "error")
    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    """
    Accept a withdrawal amount, delegate to the service layer, flash the result,
    and redirect back to /dashboard (Post/Redirect/Get pattern).
    """
    raw_amount = request.form.get("amount", "")

    # --- Route-level validation checks ---
    if not raw_amount or raw_amount.strip() == "":
        flash("Amount is required", "error")
        return redirect(url_for("dashboard"))

    try:
        amount_value = float(raw_amount)
    except ValueError:
        flash("Amount must be greater than zero", "error")
        return redirect(url_for("dashboard"))

    if amount_value <= 0:
        flash("Amount must be greater than zero", "error")
        return redirect(url_for("dashboard"))

    customer = db.session.get(Customer, session["customer_id"])
    if customer and amount_value > customer.balance:
        flash("Insufficient funds", "error")
        return redirect(url_for("dashboard"))

    success, message = svc_withdraw(session["customer_id"], raw_amount)
    flash(message, "success" if success else "error")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Custom HTTP error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Database initialisation + entry point
# ---------------------------------------------------------------------------


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
