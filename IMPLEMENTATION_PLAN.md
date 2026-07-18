# Banking Web Application — Implementation Plan

> **Status:** Planning · **Level:** High-Level Architecture & Roadmap
> **Stack:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)

---

## 1. Solution Overview

### 1.1 Objective

Build a browser-based banking web application that allows registered customers to log in securely, view their account balance, and perform basic financial transactions (deposit and withdrawal) through a clean, responsive interface.

### 1.2 Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and logout | Admin panel / bank staff portal |
| Personal dashboard | Multi-account support |
| Balance inquiry | Inter-account transfers |
| Deposit funds | Bill payments |
| Withdraw funds | External API or payment gateway integration |
| Session management | Email / SMS notifications |

### 1.3 Users

| Actor | Description |
|---|---|
| **Customer** | An existing registered bank customer who authenticates and manages their account online |

### 1.4 Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | Customer can log in using a username and password |
| FR-02 | Authenticated customer is redirected to a personal dashboard |
| FR-03 | Dashboard displays current account balance |
| FR-04 | Customer can deposit a positive monetary amount |
| FR-05 | Customer can withdraw a monetary amount not exceeding the current balance |
| FR-06 | All transactions are persisted and reflected immediately |
| FR-07 | Customer can log out and is redirected to the login page |
| FR-08 | Unauthenticated users are blocked from accessing protected pages |

### 1.5 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Passwords must be stored as secure hashes (never plain text) |
| NFR-02 | Session tokens must be server-side managed and invalidated on logout |
| NFR-03 | The UI must be responsive and usable on desktop and mobile browsers |
| NFR-04 | All backend routes that mutate state must validate inputs server-side |
| NFR-05 | The application must start with a single command and require no external services |

### 1.6 Assumptions

- Customer accounts are pre-seeded in the database; self-registration is out of scope.
- A single SQLite file serves as the data store; no database server is required.
- The application is for demonstration/workshop use and does not need HTTPS termination at the app layer.
- Bootstrap is loaded via CDN; no Node.js/npm build step is required.
- A single developer or small team will build and maintain the codebase.

---

## 2. High-Level Architecture

### 2.1 Architecture Diagram

```
┌─────────────────────────────────────────┐
│               BROWSER                   │
│                                         │
│  ┌──────────┐   ┌──────────────────┐   │
│  │  Login   │   │   Dashboard      │   │
│  │  Page    │   │  (Balance /      │   │
│  │ (HTML +  │   │  Deposit /       │   │
│  │Bootstrap)│   │  Withdraw)       │   │
│  └────┬─────┘   └────────┬─────────┘   │
│       │  HTTP Request     │             │
└───────┼───────────────────┼─────────────┘
        │                   │
        ▼                   ▼
┌───────────────────────────────────────────┐
│             FLASK BACKEND                 │
│                                           │
│  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth Routes  │  │ Account Routes   │  │
│  │ /login       │  │ /dashboard       │  │
│  │ /logout      │  │ /deposit         │  │
│  └──────┬───────┘  │ /withdraw        │  │
│         │          └────────┬─────────┘  │
│         │   Session Layer   │            │
│         └────────┬──────────┘            │
│                  │                       │
│          ┌───────▼──────┐               │
│          │  ORM / DB    │               │
│          │  Layer       │               │
│          └───────┬──────┘               │
└──────────────────┼───────────────────────┘
                   │
        ┌──────────▼──────────┐
        │   SQLite Database   │
        │   (banking.db)      │
        │                     │
        │  customers table    │
        │  transactions table │
        └─────────────────────┘
```

### 2.2 Frontend → Backend → Database Interaction

```
Frontend (HTML form)
    │
    │  POST /login  (username, password)
    ▼
Flask Route Handler
    │
    │  Query customer record by username
    ▼
SQLite  ──►  Verify password hash
    │
    │  Create server session
    ▼
Flask  ──►  Redirect to /dashboard
    │
    │  GET /dashboard  (session cookie)
    ▼
Flask  ──►  Fetch balance from DB  ──►  Render dashboard template
```

### 2.3 Request Lifecycle

1. **Browser** sends an HTTP request (GET or POST) to the Flask development server.
2. **Flask router** matches the URL to a route handler function.
3. **Route handler** checks session state; rejects unauthenticated requests.
4. **Business logic** (deposit/withdraw validation) executes within the handler.
5. **Database layer** reads or writes the SQLite file via Flask-SQLAlchemy or direct `sqlite3`.
6. **Flask** renders a Jinja2 HTML template or issues an HTTP redirect.
7. **Browser** displays the response page to the customer.

---

## 3. Component Design

### 3.1 Frontend Responsibilities

- Render login form and capture credentials for submission.
- Display the dashboard with the current balance prominently.
- Provide deposit and withdrawal forms with basic client-side input constraints (e.g., `min="0.01"`, `required`).
- Apply Bootstrap grid and component classes for responsive layout.
- Show success and error flash messages returned by the backend.
- Handle logout via a simple link or button that calls the backend logout route.

**The frontend holds no business logic and no sensitive state.** All validation and computation happens server-side.

### 3.2 Backend Responsibilities

- Serve all HTML pages via Flask route handlers and Jinja2 templates.
- Authenticate customers: compare submitted password against the stored hash.
- Manage server-side sessions (login / logout / session expiry).
- Guard every protected route with a session check decorator; redirect to login if unauthenticated.
- Validate all incoming form data (amount > 0, sufficient balance for withdrawal).
- Execute deposit and withdrawal operations atomically against the database.
- Pass flash messages to templates to report success or errors to the customer.

### 3.3 Database Responsibilities

- Persist customer identity and hashed credentials.
- Store the current account balance per customer.
- Record every deposit and withdrawal as a transaction entry (amount, type, timestamp).
- Enforce referential integrity between customers and transactions.
- Require no external server — accessed as a local file via SQLite.

---

## 4. Folder Structure

```
banking-workshop/
│
├── FRONTEND/
│   ├── templates/              # Jinja2 HTML templates served by Flask
│   │   ├── base.html           # Shared layout: Bootstrap CDN, nav, flash messages
│   │   ├── login.html          # Login form page
│   │   └── dashboard.html      # Balance display + deposit/withdraw forms
│   └── static/
│       ├── css/
│       │   └── custom.css      # Minimal overrides on top of Bootstrap
│       └── images/             # Optional brand assets
│
├── BACKEND/
│   ├── app.py                  # Flask application factory and route definitions
│   ├── models.py               # Database models (Customer, Transaction)
│   ├── auth.py                 # Authentication helpers (password hashing/verification)
│   ├── transactions.py         # Deposit and withdrawal business logic
│   ├── banking.db              # SQLite database file (generated at runtime)
│   └── requirements.txt        # Python dependencies (Flask, etc.)
│
├── IMPLEMENTATION_PLAN.md      # This document
└── docs/                       # Supporting workshop documentation
```

| Path | Responsibility |
|---|---|
| `FRONTEND/templates/` | All HTML views rendered server-side by Flask/Jinja2 |
| `FRONTEND/static/` | CSS overrides and static assets; no JS framework |
| `BACKEND/app.py` | Central application entry point; registers all routes |
| `BACKEND/models.py` | Data model definitions and database initialization |
| `BACKEND/auth.py` | Isolated authentication logic; keeps `app.py` clean |
| `BACKEND/transactions.py` | Deposit/withdraw logic separated from routing concerns |
| `BACKEND/banking.db` | Auto-generated SQLite file; excluded from version control |
| `BACKEND/requirements.txt` | Reproducible Python environment declaration |

---

## 5. Module Breakdown

### 5.1 Authentication Module

**Scope:** Login and logout flows.

| Concern | Approach |
|---|---|
| Credential verification | Hash-compare submitted password against stored hash |
| Session creation | Store `customer_id` in Flask's signed session cookie |
| Route protection | Decorator or helper checks session before each protected handler |
| Logout | Clear session data and redirect to login page |

**Key interactions:** Browser ↔ Flask `/login` route ↔ Customer table in SQLite.

---

### 5.2 Dashboard Module

**Scope:** Authenticated landing page shown immediately after login.

| Concern | Approach |
|---|---|
| Balance display | Read current balance from the Customer record in SQLite |
| Navigation | Links to deposit and withdraw forms (or inline on same page) |
| Session guard | Redirect to login if no valid session exists |

**Key interactions:** Flask `/dashboard` route ↔ Customer table ↔ `dashboard.html` template.

---

### 5.3 Account Management Module

**Scope:** Presenting accurate, up-to-date account information.

| Concern | Approach |
|---|---|
| Balance accuracy | Balance is always read fresh from the database on page load |
| Customer identity | Customer name/ID sourced from the session and Customer table |

**Key interactions:** Flask routes ↔ Customer table ↔ Jinja2 template context.

---

### 5.4 Transactions Module

**Scope:** Deposit and withdrawal operations.

| Concern | Approach |
|---|---|
| Deposit | Validate amount > 0; add to balance; insert Transaction record |
| Withdrawal | Validate amount > 0 and ≤ current balance; deduct; insert Transaction record |
| Atomicity | Both the balance update and transaction insert occur in a single DB commit |
| Feedback | Flash success or validation error message; redirect back to dashboard |

**Key interactions:** Flask `/deposit` and `/withdraw` routes ↔ `transactions.py` logic ↔ Customer + Transaction tables.

---

## 6. Implementation Roadmap

### Phase 1 — Project Scaffolding

**Goal:** Establish the folder structure, virtual environment, and a running "hello world" Flask app.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 1.1 | Create `FRONTEND/` and `BACKEND/` directory layout | Low | None |
| 1.2 | Set up Python virtual environment and `requirements.txt` | Low | None |
| 1.3 | Create `app.py` with a single health-check route | Low | 1.1, 1.2 |
| 1.4 | Verify Flask server starts and responds in browser | Low | 1.3 |

---

### Phase 2 — Database & Models

**Goal:** Define data models and initialize the SQLite database.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 2.1 | Define Customer and Transaction models in `models.py` | Medium | Phase 1 |
| 2.2 | Wire `db.init_app()` in `app.py` and create tables on startup | Low | 2.1 |
| 2.3 | Seed at least one test customer with a hashed password | Low | 2.2 |

---

### Phase 3 — Authentication

**Goal:** Working login and logout with session management.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 3.1 | Build `login.html` template with Bootstrap form | Low | Phase 1 |
| 3.2 | Implement `/login` GET/POST route in `app.py` | Medium | 2.3, 3.1 |
| 3.3 | Implement password verification in `auth.py` | Medium | 2.3 |
| 3.4 | Implement `/logout` route and session clearing | Low | 3.2 |
| 3.5 | Add route-protection decorator/helper | Low | 3.2 |

---

### Phase 4 — Dashboard & Balance

**Goal:** Authenticated customers can see their balance.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 4.1 | Build `base.html` layout with Bootstrap navbar | Low | Phase 3 |
| 4.2 | Build `dashboard.html` balance display | Low | 4.1 |
| 4.3 | Implement `/dashboard` route with session guard | Low | 3.5, 4.2 |

---

### Phase 5 — Transactions

**Goal:** Customers can deposit and withdraw funds.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 5.1 | Add deposit and withdraw form sections to `dashboard.html` | Low | Phase 4 |
| 5.2 | Implement deposit logic in `transactions.py` | Medium | Phase 2 |
| 5.3 | Implement withdrawal logic with balance check in `transactions.py` | Medium | 5.2 |
| 5.4 | Implement `/deposit` and `/withdraw` POST routes | Medium | 5.1, 5.2, 5.3 |
| 5.5 | Add flash message display to `base.html` | Low | 4.1 |

---

### Phase 6 — Polish & Validation

**Goal:** Ensure input validation, error feedback, and responsive layout are consistent.

| Step | Description | Effort | Dependency |
|---|---|---|---|
| 6.1 | Add server-side input validation to all POST routes | Medium | Phase 5 |
| 6.2 | Apply Bootstrap styling and `custom.css` refinements | Low | Phase 5 |
| 6.3 | End-to-end manual test: login → deposit → withdraw → logout | Low | All phases |

---

### Effort Legend

| Label | Meaning |
|---|---|
| **Low** | Straightforward; minimal logic or configuration |
| **Medium** | Requires design decisions or non-trivial logic |
| **High** | Complex; multiple interacting concerns |

---

*End of Implementation Plan*
