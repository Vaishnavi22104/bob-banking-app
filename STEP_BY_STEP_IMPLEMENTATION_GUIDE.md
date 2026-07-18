# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
> **Level:** Plain-English Instructions & Logic — No raw code blocks
> **Stack:** HTML + Bootstrap · Python Flask · SQLite

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing any code, confirm the following tools are installed on your machine:

- **Python 3.9 or higher** — the runtime for the Flask backend.
- **pip** — Python's package installer; ships with Python 3.
- A code editor such as **VS Code**.
- A modern web browser for manual testing.

No Node.js, npm, or external database server is needed.

---

### 1.2 Create the Project Directory Layout

Start by creating the top-level folders exactly as specified in the architecture plan. The two root-level folders are `FRONTEND` and `BACKEND`. Inside `FRONTEND`, create a `templates` subfolder and a `static/css` subfolder. Inside `BACKEND`, no subfolders are needed at this stage — all Python files will sit flat inside it.

The purpose of this separation is to keep HTML/CSS concerns completely isolated from Python/database concerns from day one.

---

### 1.3 Create and Activate a Virtual Environment

Navigate into the `BACKEND` folder in your terminal. Create a Python virtual environment there. A virtual environment is a self-contained copy of Python that keeps this project's dependencies isolated from every other Python project on your machine.

After creating it, activate the virtual environment:
- On **Windows**, run the activate script inside the `Scripts` folder of the virtual environment directory.
- On **macOS/Linux**, source the activate script inside the `bin` folder.

You will know it is active when the terminal prompt is prefixed with the virtual environment name.

> **Important:** Always activate the virtual environment before running any Python or pip command related to this project. Never install packages globally.

---

### 1.4 Declare and Install Dependencies

Create a plain-text file called `requirements.txt` inside the `BACKEND` folder. List each required package on its own line. The minimum set for this application is:

- **Flask** — the web framework.
- **Flask-SQLAlchemy** — the ORM layer that lets you define database tables as Python classes.
- **Werkzeug** — ships with Flask; provides the password hashing utilities you will use in the auth module.

Once the file is saved, run pip's install command pointing at `requirements.txt`. Pip will download and install all listed packages into the active virtual environment.

---

### 1.5 Verify the Setup

Create a minimal `app.py` in `BACKEND` that imports Flask, creates an app instance, defines a single route at `/` that returns the text "Banking App is running", and starts the development server when the file is run directly.

Run the file with Python and open your browser to `http://127.0.0.1:5000`. If you see the text, the environment is correctly configured and you can proceed.

---

## 2. Backend Implementation

### 2.1 Define the Data Models (`models.py`)

Create `models.py` inside `BACKEND`. This file is responsible for describing the shape of your data — it maps Python classes to database tables.

**Customer model** — represents a registered bank customer. The fields it needs are:
- A unique integer primary key (auto-generated).
- A username string that must be unique across all customers.
- A password hash string (never the raw password).
- A balance field stored as a decimal/float, initialised to zero by default.

**Transaction model** — represents a single deposit or withdrawal event. The fields it needs are:
- A unique integer primary key.
- A foreign key linking back to the Customer who performed it.
- A transaction type field (a string such as `"deposit"` or `"withdrawal"`).
- An amount field (always stored as a positive number).
- A timestamp that records when the transaction occurred.

The relationship between Customer and Transaction is one-to-many: one customer can have many transactions, but each transaction belongs to exactly one customer.

---

### 2.2 Create the Flask Application and Wire the Database (`app.py`)

The full `app.py` does four things in order:

1. **Create the Flask app instance** and configure it with a `SECRET_KEY` (a random string used to sign session cookies) and the `SQLALCHEMY_DATABASE_URI` pointing to a `banking.db` file inside the `BACKEND` folder.

2. **Initialise the ORM** by passing the Flask app to the SQLAlchemy object you imported from `models.py`.

3. **Register all route handlers** (described in sections 2.4–2.7 below).

4. **Create the database tables** by calling the ORM's create-all method inside the application context when the app starts for the first time. This is safe to call every time — it only creates tables that do not already exist.

---

### 2.3 Seed the Database with a Test Customer

Because self-registration is out of scope, you need at least one customer record in the database before you can log in. Write a small seed function (either in `app.py` or a separate `seed.py` script) that:

1. Checks whether a customer with your chosen test username already exists.
2. If not, hashes a test password using Werkzeug's `generate_password_hash` function.
3. Creates a new Customer object with that username, the hash, and a starting balance (for example, 1000.00).
4. Adds it to the database session and commits.

Run this seed function once before your first login attempt.

---

### 2.4 Authentication Routes (`/login` and `/logout`)

**`/login` — GET request:**
Simply render the `login.html` template. If the user is already logged in (check for `customer_id` in the session), redirect them straight to `/dashboard` instead of showing the login form again.

**`/login` — POST request:**
This is where authentication logic runs. The flow is:
1. Read the `username` and `password` values from the submitted form.
2. Query the Customer table for a row whose username matches.
3. If no matching customer is found, flash an error message ("Invalid credentials") and re-render the login page.
4. If a customer is found, call Werkzeug's `check_password_hash` function, passing the stored hash and the submitted password. This function returns `True` or `False`.
5. If it returns `False`, flash the same generic error and re-render — never tell the user which of the two fields was wrong.
6. If it returns `True`, store the customer's integer ID in `session["customer_id"]` and redirect to `/dashboard`.

**`/logout` — GET request:**
Clear the entire session dictionary and redirect to `/login`. No template rendering needed — this is always a redirect.

---

### 2.5 Route Protection (Login-Required Guard)

Every route except `/login` and `/logout` must be protected. The cleanest way to do this is to write a helper function (or a Python decorator) that:

1. Checks whether `"customer_id"` exists in the Flask session.
2. If it does not exist, redirects the caller to `/login`.
3. If it does exist, allows the original route function to proceed.

Apply this guard to `/dashboard`, `/deposit`, and `/withdraw`. This satisfies FR-08 from the functional requirements.

---

### 2.6 Dashboard Route (`/dashboard`)

**`/dashboard` — GET request:**
1. Apply the login-required guard.
2. Read `session["customer_id"]` to know which customer is logged in.
3. Query the Customer table by that ID to get the customer's name and current balance.
4. Pass the name and balance as template variables when rendering `dashboard.html`.

The balance must always be fetched fresh from the database — never store it in the session, because transactions can change it.

---

### 2.7 Transaction Routes (`/deposit` and `/withdraw`)

Both routes accept only POST requests (they mutate state). Both follow the same overall pattern but with different validation logic.

**`/deposit` — POST:**
1. Apply the login-required guard.
2. Read the `amount` value from the form.
3. Pass it through the deposit service function in `transactions.py` (described next).
4. Flash the success or error message returned by the service.
5. Redirect back to `/dashboard` regardless of outcome.

**`/withdraw` — POST:**
1. Apply the login-required guard.
2. Read the `amount` value from the form.
3. Also fetch the customer's current balance from the database (needed for the balance check).
4. Pass both to the withdrawal service function in `transactions.py`.
5. Flash the success or error message.
6. Redirect back to `/dashboard`.

Both routes must redirect (not render a template) after processing. This prevents the browser from re-submitting the form if the user refreshes the page (known as the Post/Redirect/Get pattern).

---

### 2.8 Transaction Service Logic (`transactions.py`)

This file contains pure business logic — no Flask routing, no template rendering. It receives data, performs operations on the database, and returns a result (such as a success/failure flag and a message string).

**Deposit service function:**
- Accept the customer ID and the raw amount value from the form.
- Attempt to convert the amount to a float. If conversion fails (the user typed letters), return a failure result.
- Check that the converted amount is greater than zero. If not, return a failure result.
- Load the Customer record by ID.
- Add the amount to the customer's current balance.
- Create a new Transaction record with type `"deposit"`, the amount, and the current timestamp.
- Add both changes to the database session and commit in a single transaction.
- Return a success result.

**Withdrawal service function:**
- Accept the customer ID and the raw amount value.
- Attempt to convert and validate the amount (same as deposit).
- Load the Customer record.
- Check that the amount does not exceed the current balance. If it does, return a failure result with an "insufficient funds" message.
- Subtract the amount from the balance.
- Create a new Transaction record with type `"withdrawal"`.
- Commit both changes in a single database transaction.
- Return a success result.

The reason both operations are committed together in one call is **atomicity**: if anything fails mid-way (e.g. a disk error), neither the balance change nor the transaction record will be partially saved.

---

### 2.9 Authentication Helper (`auth.py`)

Keep password-related logic in its own file to avoid cluttering `app.py`. This file exposes two functions:

- **`hash_password(raw_password)`** — wraps Werkzeug's `generate_password_hash`. Called only during seeding.
- **`verify_password(stored_hash, submitted_password)`** — wraps Werkzeug's `check_password_hash`. Called during login. Returns `True` or `False`.

Using Werkzeug's built-in functions means you get salted hashing (bcrypt or PBKDF2) for free without writing any cryptographic code yourself.

---

### 2.10 Error Handling

At the Flask application level, register custom error handler functions for the two most common HTTP errors:

- **404 Not Found** — render a simple "Page not found" template or return a plain message.
- **500 Internal Server Error** — render a "Something went wrong" template or plain message.

For all user-facing validation errors inside routes (wrong password, invalid amount, insufficient funds), use Flask's `flash()` mechanism rather than HTTP error codes. Flash messages are stored in the session for one request and displayed in the template, giving the user a friendly inline message without leaving the page.

---

## 3. Frontend Implementation

### 3.1 Configure Flask to Find the Templates and Static Files

By default, Flask looks for templates in a folder called `templates` and static files in a folder called `static` relative to where `app.py` lives. Because this project places them inside `FRONTEND/`, you must tell Flask their actual locations when creating the app instance. Pass the `template_folder` and `static_folder` arguments pointing to the correct paths inside `FRONTEND/`.

---

### 3.2 Base Layout Template (`base.html`)

This file is the master shell that all other pages inherit from. Build it to contain:

- The full HTML boilerplate (`<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`).
- A `<meta name="viewport">` tag so Bootstrap's responsive grid works on mobile.
- The Bootstrap CSS link loaded from the official Bootstrap CDN (no download needed).
- A `<title>` block that child templates can override.
- A Bootstrap **navbar** at the top showing the bank name on the left and a "Logout" link on the right. The logout link should only appear when the user is logged in (use a Jinja2 `if` check on the session variable).
- A **flash messages block** below the navbar that loops over all pending messages and renders each one as a Bootstrap alert. Use the "success" alert class for success messages and the "danger" class for errors.
- A main content `{% block content %}{% endblock %}` placeholder where child templates inject their page-specific HTML.

---

### 3.3 Login Page (`login.html`)

This page extends `base.html` and fills the content block with a login form. Design guidance:

- Center the form card horizontally on the page using Bootstrap's grid (`offset` columns or flexbox utility classes).
- The card should have a heading ("Sign In" or "Customer Login"), the two form fields, and a submit button.
- The **username field** is a standard text input. Mark it as `required`.
- The **password field** is a password-type input so the browser masks the characters. Mark it as `required`.
- The form's `action` attribute points to `/login` and the method is `POST`.
- The submit button uses Bootstrap's primary button style.
- No JavaScript is needed — the form submits natively.

Flash messages from the base layout will appear above the card if the login fails.

---

### 3.4 Dashboard Page (`dashboard.html`)

This page extends `base.html` and is the main authenticated view. It is divided into three visual sections:

**Balance Section:**
- A prominent card or jumbotron at the top displaying the customer's name and their current balance.
- The balance should be formatted with a currency symbol and two decimal places. Use Jinja2's built-in `| round` filter or Python's string formatting passed from the route.
- Style this section to stand out — use a Bootstrap info or success card colour.

**Deposit Form Section:**
- A Bootstrap card with the title "Deposit Funds".
- A single numeric input field labelled "Amount". Set `min="0.01"` and `step="0.01"` as HTML attributes to give basic browser-level hints.
- A "Deposit" submit button in green (Bootstrap success style).
- The form `action` points to `/deposit`, method is `POST`.

**Withdraw Form Section:**
- Identical structure to the deposit form but titled "Withdraw Funds".
- The form `action` points to `/withdraw`, method is `POST`.
- The submit button uses Bootstrap's warning or danger colour to visually signal that this is a debit action.

All three sections should sit in a single responsive Bootstrap column layout so that on large screens they appear side by side or stacked cleanly, and on small screens they stack vertically.

---

### 3.5 Custom CSS (`custom.css`)

Keep this file minimal — its job is only to override or supplement Bootstrap defaults. Useful additions include:

- Increasing the balance figure's font size so it reads as the most important number on the page.
- Adding a small top margin below the navbar so page content does not crowd it.
- Setting a subtle background colour on the `<body>` to distinguish the app from a blank white page.

Do not replicate styles that Bootstrap already provides. Use Bootstrap utility classes in HTML first, and only write custom CSS when no utility class exists.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Templates Folder

As described in section 3.1, the Flask app instance must be created with explicit `template_folder` and `static_folder` path arguments that point into `FRONTEND/`. Once this is configured, every call to `render_template("login.html")` inside your route handlers will correctly resolve to `FRONTEND/templates/login.html`.

Use Python's `os.path` module to build the path relative to `app.py`'s location so the paths work regardless of which directory you launch the server from.

---

### 4.2 Connect Flask to SQLite via SQLAlchemy

The connection is configured through a single URI string assigned to Flask's `SQLALCHEMY_DATABASE_URI` config key. The URI format for SQLite is `sqlite:///` followed by the absolute path to the `.db` file. Use `os.path.join` with `os.path.abspath` to construct this path so the database file always lands inside the `BACKEND` folder.

After configuration, `db.create_all()` (called inside the application context at startup) reads the models you defined in `models.py` and creates the corresponding tables in `banking.db` if they do not exist. You never write a `CREATE TABLE` SQL statement manually.

---

### 4.3 Connect HTML Forms to Backend Routes

Each HTML form in the frontend communicates with the backend through its `action` and `method` attributes:

- The login form posts to `/login` — Flask's login POST handler reads `request.form["username"]` and `request.form["password"]`.
- The deposit form posts to `/deposit` — Flask reads `request.form["amount"]`.
- The withdraw form posts to `/withdraw` — Flask reads `request.form["amount"]`.

The `name` attribute on each HTML input element must exactly match the key you use in `request.form` on the backend. If the HTML input has `name="amount"` but you read `request.form["amt"]` in Flask, the value will be missing. Verify these names match on both sides before testing.

---

### 4.4 Pass Data from Flask Routes to Templates

When Flask renders a template, it can pass Python variables as keyword arguments to `render_template`. Inside the template, Jinja2 makes those variables available by the same name.

For the dashboard, pass the customer's full name and their current balance as separate variables. In the template, reference them with `{{ customer_name }}` and `{{ balance }}`. This is the entire bridge between the database query in the route and the display in the browser.

---

### 4.5 Flash Messages End-to-End

The flash message system works across three layers:

1. **Backend route** calls `flash("message text", "category")` before redirecting. Category is a string like `"success"` or `"error"`.
2. **Flask session** stores the message temporarily for the next request only.
3. **`base.html` template** calls `get_flashed_messages(with_categories=True)` in a Jinja2 loop and renders each message as a Bootstrap alert whose colour class matches the category.

Because `base.html` is inherited by all pages, flash messages will automatically appear on whichever page the user lands on after the redirect — you do not need to add the flash block to each individual template.

---

## 5. Validation Rules

Validation happens at two layers: the browser (light, for usability) and the server (authoritative, for security). Server-side validation is what actually enforces the rules — browser-side validation can always be bypassed.

### 5.1 Login Validation

| Rule | Where enforced | Behaviour on failure |
|---|---|---|
| Username must not be empty | Browser (`required`) and server | Flash generic "Invalid credentials"; re-render login |
| Password must not be empty | Browser (`required`) and server | Flash generic "Invalid credentials"; re-render login |
| Username must exist in the database | Server only | Flash "Invalid credentials"; re-render login |
| Password must match the stored hash | Server only | Flash "Invalid credentials"; re-render login |

> **Security note:** Always return the same error message regardless of whether the username was wrong or the password was wrong. This prevents an attacker from using different error messages to enumerate valid usernames (a technique called username enumeration).

---

### 5.2 Balance Validation

| Rule | Where enforced | Behaviour on failure |
|---|---|---|
| Balance is read fresh from DB on every page load | Server only | N/A — this is an implementation rule, not user input |
| Balance is never stored or cached in the session | Server only | N/A — enforced by design |
| Balance is displayed with exactly two decimal places | Template | N/A — formatting only |

---

### 5.3 Deposit Validation

| Rule | Where enforced | Behaviour on failure |
|---|---|---|
| Amount field must not be empty | Browser (`required`) and server | Flash "Please enter an amount"; redirect to dashboard |
| Amount must be a valid number | Server | Flash "Amount must be a valid number"; redirect |
| Amount must be greater than zero | Server | Flash "Deposit amount must be greater than zero"; redirect |
| Amount must have at most two decimal places | Server (optional but recommended) | Flash "Amount cannot have more than two decimal places"; redirect |

The server should always attempt to parse the raw string from the form before doing any arithmetic. Never assume the browser's `type="number"` attribute will prevent non-numeric input.

---

### 5.4 Withdrawal Validation

| Rule | Where enforced | Behaviour on failure |
|---|---|---|
| Amount field must not be empty | Browser (`required`) and server | Flash "Please enter an amount"; redirect |
| Amount must be a valid number | Server | Flash "Amount must be a valid number"; redirect |
| Amount must be greater than zero | Server | Flash "Withdrawal amount must be greater than zero"; redirect |
| Amount must not exceed current balance | Server | Flash "Insufficient funds. Your balance is £X.XX"; redirect |

The insufficient funds check must compare the parsed amount against the balance that is read from the database within the same request — never compare against a balance value that came from the form or the session.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual functions in isolation without starting a web server or touching the real database.

**What to unit test:**

- **`auth.py` — `hash_password` and `verify_password`:** Confirm that hashing a password and then verifying it returns `True`. Confirm that verifying the wrong password returns `False`. Confirm that the stored hash is never equal to the raw password string.

- **`transactions.py` — deposit service:** Test with a valid positive amount and confirm the balance increases by the correct amount. Test with zero and confirm it fails. Test with a negative number and confirm it fails. Test with a non-numeric string and confirm it fails.

- **`transactions.py` — withdrawal service:** Test a valid withdrawal where sufficient balance exists. Test a withdrawal equal to the full balance (edge case — should succeed). Test a withdrawal exceeding the balance and confirm it fails with the correct message. Test zero and non-numeric inputs.

Use Python's built-in `unittest` module or the `pytest` framework. For tests that interact with the database, use Flask's `app.test_request_context()` and point the database URI at a separate in-memory SQLite database (`sqlite:///:memory:`) so unit tests never touch the real `banking.db` file.

---

### 6.2 Integration Tests

Integration tests verify that the full request-response cycle works correctly — form submission → route → database → redirect/render.

**What to integration test:**

- **Login flow:** POST to `/login` with correct credentials → confirm redirect to `/dashboard` and session contains `customer_id`. POST with wrong password → confirm redirect to `/login` and session does not contain `customer_id`.

- **Session guard:** GET `/dashboard` without being logged in → confirm redirect to `/login`.

- **Deposit flow:** Log in as the test customer, POST a valid amount to `/deposit`, GET `/dashboard` → confirm the displayed balance has increased by the correct amount.

- **Withdraw flow:** Log in, POST a valid withdrawal amount to `/withdraw`, confirm balance decreased. POST an amount exceeding the balance, confirm balance is unchanged and the flash message mentions "insufficient funds".

- **Logout flow:** Log in, GET `/logout`, attempt to GET `/dashboard` → confirm redirect to `/login`.

Use Flask's built-in test client (`app.test_client()`) to send requests without a real network connection. Use an in-memory SQLite database for these tests and seed it with a known test customer at the start of each test.

---

### 6.3 Manual Testing Checklist

Run through each of these scenarios in a real browser before considering the implementation complete:

**Authentication**
- [ ] Open the app in a browser — you are on the login page.
- [ ] Submit the login form with the correct username and password — you are redirected to the dashboard.
- [ ] Manually type `/dashboard` in the address bar while logged out — you are redirected to login.
- [ ] Submit the login form with a wrong password — you see an error message and stay on the login page.
- [ ] Click the logout link on the dashboard — you are redirected to login; pressing the browser back button does not return you to the dashboard.

**Balance Display**
- [ ] After login the balance displayed matches the seeded starting value.
- [ ] After a deposit the balance shown on the dashboard reflects the new amount.
- [ ] After a withdrawal the balance shown reflects the new amount.

**Deposit**
- [ ] Enter a valid positive amount and submit — success message appears, balance increases.
- [ ] Enter zero and submit — error message appears, balance unchanged.
- [ ] Enter a negative number and submit — error message appears.
- [ ] Leave the field empty and submit — browser prevents submission (or server returns an error).
- [ ] Enter letters and submit — error message appears, balance unchanged.

**Withdrawal**
- [ ] Enter a valid amount less than the balance — success message, balance decreases.
- [ ] Enter the exact balance amount — success message, balance becomes zero.
- [ ] Enter more than the balance — "insufficient funds" error, balance unchanged.
- [ ] Enter zero or a negative value — error message, balance unchanged.

**Responsive Layout**
- [ ] Resize the browser window to a narrow width — forms and balance card stack vertically and remain readable.
- [ ] Open the app on a mobile device or browser devtools mobile simulation — layout does not overflow horizontally.

---

## 7. Deployment

### 7.1 Running Locally

Follow these steps each time you want to run the application on your development machine:

1. Open a terminal and navigate to the `BACKEND` folder.
2. Activate the virtual environment (see section 1.3).
3. If this is the first run, run the seed script to populate the test customer.
4. Run `python app.py`. Flask's development server starts on `http://127.0.0.1:5000`.
5. Open that URL in your browser.
6. To stop the server, press `Ctrl + C` in the terminal.

> **Never use Flask's built-in development server in production.** It is single-threaded, not hardened against attacks, and Flask itself prints a warning to this effect when it starts.

---

### 7.2 Environment Variables

Before moving beyond local development, move sensitive configuration values out of `app.py` and into environment variables:

- **`SECRET_KEY`** — the string used to sign session cookies. On your local machine you can hard-code a value for convenience, but in any shared or deployed environment this must be a long, random, secret string set as an environment variable.
- **`DATABASE_URL`** — the path to the SQLite file. While SQLite is a local file and less sensitive, keeping the path configurable makes the app easier to move.

Python's `os.environ.get("KEY", "default_value")` pattern is the standard way to read environment variables with a fallback for local development.

---

### 7.3 Production Considerations

| Concern | What to do |
|---|---|
| **WSGI server** | Run the app behind a production WSGI server such as **Gunicorn** (Linux/macOS) or **Waitress** (Windows). These servers are multi-threaded and production-hardened, unlike Flask's built-in server. |
| **HTTPS** | Place a reverse proxy such as **Nginx** or **Caddy** in front of the WSGI server. Configure TLS certificates there. Never run banking software over plain HTTP in production. |
| **Secret key** | Generate a cryptographically random secret key (e.g. using Python's `secrets.token_hex(32)`) and store it as an environment variable — never commit it to version control. |
| **Debug mode** | Ensure `app.run(debug=False)` or that the `FLASK_DEBUG` environment variable is not set to `1`. Debug mode exposes an interactive debugger to anyone who can reach the server. |
| **Database** | SQLite is suitable for a single-server demo. For multi-user or multi-process production loads, migrate to PostgreSQL or MySQL and update the `SQLALCHEMY_DATABASE_URI` accordingly. |
| **Static files** | In production, configure Nginx to serve the contents of `FRONTEND/static/` directly, rather than routing static file requests through Flask. This is faster and reduces load on the Python process. |
| **Dependency pinning** | Before deploying, run `pip freeze > requirements.txt` to capture exact version numbers of all installed packages. This ensures the production environment is identical to development. |

---

*End of Step-by-Step Implementation Guide*
