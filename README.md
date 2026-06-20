# Financial Dashboard

A self-hosted personal finance aggregation dashboard. Import bank and credit card statements as PDFs or CSVs, automatically categorize transactions, and visualize spending trends over time.

## Features

- **Multi-format statement import** — PDF and CSV support for Capital One bank accounts, Amex year-end summaries, and Amex monthly statements
- **Auto-categorization** — rules-based engine classifies transactions on import using regex patterns against payee/description
- **Category management** — create, rename, recolor, delete, and merge categories; bulk-move all transactions between categories
- **Transaction management** — filter by date, category, source, amount, and free-text search; bulk reassign categories across multiple transactions at once; inline single-row category editing without losing scroll position
- **Uncategorized filter** — quickly surface any transaction that hasn't been classified yet
- **Double-counting prevention** — credit card payments in bank statements are automatically tagged as transfers, not expenses
- **Charts** — spending by category (donut), monthly income/expense/net trend (line), top spending categories (bar)
- **Dark mode** — system-aware with manual toggle
- **CSV export** — export the current filtered transaction view

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS + Recharts |
| Backend | FastAPI + SQLAlchemy (async-compatible) |
| Database | MariaDB |
| PDF parsing | pdfplumber |
| Runtime | Docker Compose (`python:3.11-slim`, no custom image) |
| Proxy | NGINX (serves static frontend, proxies `/api/` → backend) |

## Supported Statement Formats

| Format | Source | Detection |
|---|---|---|
| Capital One checking — PDF | Bank | Content scan for "capital one" |
| Capital One checking — CSV | Bank | Header column match |
| Amex year-end summary | Credit card | Content scan for "year-end summary" |
| Amex monthly statement | Credit card | Content scan for closing date pattern |

## Project Structure

```
financial-dashboard/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI app, lifespan startup, CORS
│       ├── models.py         # SQLAlchemy models
│       ├── schemas.py        # Pydantic request/response schemas
│       ├── categorizer.py    # Rules engine + default seed data
│       ├── database.py       # DB connection
│       ├── routes/
│       │   ├── analytics.py  # Summary, by-category, trends, top spenders
│       │   ├── categories.py # CRUD + move-transactions + merge
│       │   ├── transactions.py
│       │   ├── uploads.py
│       │   └── debug.py      # Raw PDF text extraction for diagnostics
│       └── parsers/
│           ├── bank_parser.py
│           ├── capital_one_parser.py
│           ├── capital_one_csv_parser.py
│           ├── credit_card_parser.py
│           ├── amex_parser.py
│           ├── amex_monthly_parser.py
│           ├── payroll_parser.py
│           └── pdf_parser.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── Dashboard.jsx
│           ├── Categories.jsx
│           ├── Filters.jsx
│           ├── Summary.jsx
│           ├── TransactionTable.jsx
│           ├── Upload.jsx
│           └── Charts/
│               ├── CategoryPie.jsx
│               ├── MonthlyTrend.jsx
│               └── TopSpenders.jsx
└── docker-compose.yml
```

## Setup

### Prerequisites

- Docker + Docker Compose
- MariaDB instance (external; the app creates its own tables on startup)
- NGINX (for serving the frontend and proxying the API)

### Database

Create the database and user before starting the container:

```sql
CREATE DATABASE financial_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'finuser'@'%' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON financial_dashboard.* TO 'finuser'@'%';
FLUSH PRIVILEGES;
```

The application creates all tables and seeds default categories/rules on first startup.

### Environment

Copy and fill in `.env`:

```env
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=finuser
DB_PASSWORD=yourpassword
DB_NAME=financial_dashboard
BACKEND_PORT=8000
ENVIRONMENT=production
```

### Backend

```bash
docker compose up -d
```

The container installs dependencies on startup (~30s first run). Uvicorn runs with `--reload` so Python file changes hot-reload without a restart. A full container restart is only needed when `requirements.txt` changes.

### Frontend

Build the static files and deploy them to wherever NGINX serves from:

```bash
cd frontend
VITE_API_URL=/api npm run build
# copy dist/ to your web root
```

### NGINX

Minimal config to serve the frontend and proxy the API:

```nginx
server {
    listen 80;

    root /var/www/financial-dashboard;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Categorization

Default categories and regex rules are seeded on startup. Rules can be managed via the API (`GET/POST /categories/rules`). The engine evaluates rules in priority order; first match wins.

Amex statements use the card issuer's own categorization (section headers on year-end, MCC hints on monthly) which bypasses the regex engine for more accurate classification.

## Resetting Data

To wipe all transactions and upload history while keeping categories and rules:

```sql
TRUNCATE TABLE transactions;
TRUNCATE TABLE upload_history;
```

## API

The backend is a standard FastAPI app. Interactive docs are available at `http://localhost:8000/docs` when running locally.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Import a PDF or CSV statement |
| `GET` | `/transactions` | List with filtering and pagination |
| `PUT` | `/transactions/bulk-category` | Bulk reassign category |
| `GET` | `/categories` | List with transaction counts |
| `PUT` | `/categories/{id}` | Rename / recolor |
| `DELETE` | `/categories/{id}` | Delete, optionally reassigning transactions |
| `POST` | `/categories/{id}/move-transactions` | Move all transactions to another category |
| `GET` | `/analytics/summary` | Total income, expenses, net |
| `GET` | `/analytics/by-category` | Spending breakdown |
| `GET` | `/analytics/monthly-trend` | Month-by-month income/expense/net |
| `GET` | `/analytics/top-spenders` | Top N categories by spend |
| `POST` | `/debug/parse-pdf` | Return raw pdfplumber text (diagnostics) |
