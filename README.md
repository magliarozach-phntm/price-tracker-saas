# 📈 MAG PriceWatch

MAG PriceWatch is a full-stack price monitoring SaaS application built with Python and FastAPI.

The application allows users to create accounts, track products, define target prices, perform live price checks, monitor price history, and receive automated alerts when tracked products reach desired prices.

The application is deployed in production on Railway with PostgreSQL persistence and uses Playwright-powered browser automation for JavaScript-rendered retailer pages.

---

## 🚀 Features

### 👤 User Accounts

- User registration and authentication
- Secure password hashing
- Session-based authentication
- User-specific product tracking
- Configurable user timezone
- Protected dashboard and product routes

### 📦 Product Tracking

Users can:

- Add products by URL
- Set custom target prices
- Edit tracked products
- Delete tracked products
- Perform an immediate **Check Now**
- Monitor current price
- View stock availability
- See the difference between current and target price
- Track historical price checks

### 🎯 Retailer Support

| Retailer | URL Support | Live Price Tracking |
|---|---:|---:|
| Target | ✅ | ✅ |
| Amazon | ✅ | 🚧 Coming Soon |

Target product pages are rendered using a headless Chromium browser through Playwright, allowing MAG PriceWatch to retrieve pricing information from JavaScript-rendered product pages.

Amazon URLs can be added to the application, but active Amazon price monitoring is currently disabled while a reliable production integration is developed.

---

## 🔍 Live Target Price Monitoring

MAG PriceWatch uses Playwright and headless Chromium to load Target product pages in a real browser environment.

The tracking pipeline is:

```text
Target Product URL
        ↓
Retailer Dispatcher
        ↓
Target Scraper
        ↓
Playwright / Chromium
        ↓
Rendered Product Page
        ↓
Price + Availability Extraction
        ↓
Tracking Service
        ↓
PostgreSQL
        ↓
MAG PriceWatch Dashboard
```

This approach allows the application to work with product information that is populated dynamically through JavaScript rather than being available in the initial HTML response.

---

## ⏱️ Automated Monitoring

MAG PriceWatch includes background scheduling through APScheduler.

The scheduler integrates with the same tracking service used by manual **Check Now** requests, allowing tracked products to be checked automatically.

The architecture is designed so manual and scheduled checks share the same tracking pipeline.

```text
APScheduler
     ↓
Tracked Products
     ↓
Retailer Scraper
     ↓
Price / Stock Result
     ↓
Price History
     ↓
Alert Evaluation
```

---

## 🔔 Price & Stock Alerts

The tracking service supports automated email notifications.

### Price Alerts

When:

```text
Current Price <= Target Price
```

MAG PriceWatch can notify the user that their target price has been reached.

The application also tracks the last alerted price to prevent unnecessary duplicate alerts.

### Back-in-Stock Alerts

The application compares the previous stock state with the latest result.

When a product transitions from:

```text
Out of Stock → In Stock
```

a stock notification can be sent to the user.

---

## 📊 Price History

Successful product checks are persisted to the database.

Each price history record stores:

- Product
- Price
- Check timestamp

This provides the foundation for historical price analytics and future price trend visualization.

---

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Starlette
- Uvicorn

### Database

- PostgreSQL — Production
- SQLite — Automated testing

### Web

- Jinja2
- HTML
- CSS
- FastAPI server-side rendering

### Browser Automation

- Playwright
- Headless Chromium
- BeautifulSoup

### Background Processing

- APScheduler

### Database Migrations

- Alembic

### Authentication & Validation

- SessionMiddleware
- Secure password hashing
- Pydantic validation
- Email validation

### Deployment

- Railway
- Railpack
- PostgreSQL
- GitHub

### Testing

- pytest
- FastAPI TestClient
- SQLAlchemy in-memory SQLite test database

---

## 🏗️ Project Architecture

```text
price-tracker-saas/
│
├── alembic/
│   └── versions/
│
├── app/
│   ├── api/
│   │   ├── api_auth.py
│   │   ├── api_products.py
│   │   ├── api_tracker.py
│   │   └── server.py
│   │
│   ├── core/
│   │   ├── database.py
│   │   ├── emailer.py
│   │   └── security.py
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── scheduler/
│   │   ├── scrapers/
│   │   │   ├── amazon.py
│   │   │   ├── base.py
│   │   │   └── target.py
│   │   ├── tracking/
│   │   ├── product_validation.py
│   │   └── scraper.py
│   │
│   ├── static/
│   │   └── css/
│   │
│   ├── templates/
│   │
│   └── web/
│       ├── auth.py
│       ├── context.py
│       ├── dashboard.py
│       ├── flash.py
│       ├── home.py
│       ├── products.py
│       └── settings.py
│
├── tests/
│
├── alembic.ini
├── requirements.txt
└── README.md
```

The application separates API routes, web routes, persistence, scraping, tracking, scheduling, validation, and presentation into dedicated modules.

---

## 🗄️ Database Architecture

MAG PriceWatch uses SQLAlchemy for ORM-based database access.

Production uses PostgreSQL through a configurable environment variable:

```env
DATABASE_URL=postgresql+psycopg://...
```

Database sessions are provided through FastAPI dependency injection.

Alembic manages schema migrations:

```bash
alembic upgrade head
```

Railway runs migrations against the production PostgreSQL database as part of the deployment process.

---

## 🧪 Testing

The project includes an automated pytest suite covering major application functionality.

Current test status:

```text
30 passed
```

Tests use an isolated in-memory SQLite database:

```text
sqlite+pysqlite:///:memory:
```

with SQLAlchemy's `StaticPool`.

This keeps automated tests isolated from the production PostgreSQL database.

Run the complete suite with:

```bash
pytest -v
```

---

## 💻 Local Development

### 1. Clone the repository

```bash
git clone https://github.com/magliarozach-phntm/price-tracker-saas.git
cd price-tracker-saas
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Chromium for Playwright

```bash
playwright install chromium
```

On supported Linux environments where browser dependencies are also required:

```bash
playwright install --with-deps chromium
```

### 5. Configure environment variables

Create a `.env` file.

Example:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
HTTPS_ONLY=False
```

Additional email configuration may be required for notification functionality.

> Never commit `.env` files, database credentials, API keys, or application secrets to GitHub.

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Start the application

```bash
uvicorn app.api.server:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

---

## ☁️ Production Deployment

MAG PriceWatch is deployed on Railway.

Production consists of:

```text
GitHub
   ↓
Railway / Railpack
   ↓
Python Environment
   ↓
Playwright + Chromium
   ↓
Alembic Migrations
   ↓
FastAPI / Uvicorn
   ↓
PostgreSQL
```

The production server runs with:

```bash
uvicorn app.api.server:app --host 0.0.0.0 --port $PORT
```

Playwright requires a Chromium browser binary in addition to the Python package.

The Railway build therefore installs Chromium and its required Linux dependencies:

```bash
playwright install --with-deps chromium
```

---

## 🔐 Security

The application includes:

- Password hashing
- Session-based authentication
- Protected user routes
- Per-user product ownership validation
- Environment-based secrets
- Server-side validation
- Database-backed user accounts
- HTTPS-aware session configuration

Sensitive credentials are supplied through environment variables rather than stored in source control.

---

## 🗺️ Roadmap

Planned development includes:

- [x] FastAPI backend
- [x] User registration
- [x] User login/logout
- [x] Session authentication
- [x] Product CRUD
- [x] Target price configuration
- [x] Manual price checks
- [x] Target URL support
- [x] Live Target price extraction
- [x] Playwright browser automation
- [x] PostgreSQL production database
- [x] Alembic migrations
- [x] Railway deployment
- [x] Price history
- [x] Stock-state tracking
- [x] APScheduler integration
- [x] Automated test suite
- [ ] Production verification of scheduled price checks
- [ ] Amazon price tracking
- [ ] Additional retailer integrations
- [ ] Historical price charts
- [ ] Improved analytics
- [ ] Notification preferences
- [ ] Expanded API functionality
- [ ] Docker deployment
- [ ] CI/CD test automation

---

## 🎯 Project Purpose

MAG PriceWatch began as a Python price-tracking project and has evolved into a deployed full-stack application.

The project is intended to demonstrate practical experience with:

- Backend software engineering
- REST API development
- Relational databases
- ORM architecture
- Database migrations
- Browser automation
- Web scraping
- Authentication
- Background scheduling
- Automated testing
- Cloud deployment
- Production debugging
- Modular application architecture

It also demonstrates the transition from a locally running Python application to a persistent, database-backed production web service.

---

## 👨‍💻 Author

**Zach Magliaro**

Software Engineering • Backend Development • Automation • Cloud

GitHub:  
https://github.com/magliarozach-phntm

LinkedIn:  
https://linkedin.com/in/zacharymagliaro

---

## 📄 License

This project is currently maintained as a portfolio and educational software engineering project.
