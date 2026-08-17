# MAG PriceWatch

A production-deployed price tracking SaaS application built with **FastAPI, PostgreSQL, SQLAlchemy, Alembic, APScheduler, Jinja2, and BeautifulSoup**.

MAG PriceWatch allows users to create accounts, track products, set target prices, monitor price and stock changes, view product analytics, and receive automated email alerts when tracked products meet configured conditions.

> Originally inspired by a Python price-tracking project and rebuilt into a full-stack, multi-user SaaS application.

---

## Live Application

MAG PriceWatch is deployed on Railway.

**Live Demo:**  
`ADD_YOUR_RAILWAY_URL_HERE`

---

## Features

### User Accounts

MAG PriceWatch supports individual user accounts with:

- User registration
- Secure password hashing
- Session-based authentication
- Login and logout
- Change-password functionality
- User-specific product ownership
- Configurable user timezone
- Secure HTTPS-only production cookies

Tracked products are associated with their owner so authenticated users only interact with their own products.

---

### Product Tracking

Authenticated users can:

- Add products to their watchlist
- Set a target price
- Edit tracked products
- Delete tracked products
- Manually trigger a price check
- Monitor current price
- Monitor stock availability
- View the last check time
- View individual product analytics

---

### Automated Price Monitoring

MAG PriceWatch includes background price checking powered by **APScheduler**.

The tracking pipeline is designed to:

1. Retrieve tracked products from PostgreSQL
2. Send products through the appropriate retailer scraper
3. Determine current price and availability
4. Update product state
5. Store successful price observations
6. Evaluate price-alert conditions
7. Evaluate back-in-stock conditions
8. Send email notifications when appropriate

Individual product failures are isolated so one failed retailer request does not stop checks for other tracked products.

---

### Price Alerts

Users can assign a target price to each tracked product.

When a successful check returns a price at or below the target price, MAG PriceWatch can send an email notification.

The application also stores alert information to help prevent unnecessary duplicate price notifications.

---

### Stock Monitoring

Tracked products maintain an availability state.

MAG PriceWatch can distinguish between:

- In stock
- Out of stock
- Availability unknown

When a product transitions from out of stock back to in stock, the tracking service can send a back-in-stock notification.

---

### Price History

Successful price observations are stored separately from the current product state.

This allows the application to retain historical pricing information rather than simply replacing the previous price each time a check runs.

Product analytics can use this history to calculate and display information such as:

- Current price
- Target price
- Historical prices
- Lowest recorded price
- Highest recorded price
- Average recorded price
- Stock status
- Last checked time

---

## Retailer Architecture

The scraping layer uses a modular retailer architecture.

```text
app/services/scrapers/
├── amazon.py
├── base.py
├── bestbuy.py
├── ebay.py
├── target.py
└── walmart.py
```

Retailer-specific scraping logic is separated from the main tracking service.

The application dispatches a product URL to the appropriate scraper, which returns a standardized result containing information such as:

```text
success
retailer
price
in_stock
status_code
page_title
error
```

This keeps the tracking system independent from individual retailer implementations and makes additional retailer support easier to develop.

### Current Retailer Support

**Amazon is currently the primary supported retailer.**

Additional retailer modules are included in the project architecture and are under development.

Retailer websites can change their HTML structure or restrict automated requests, so production scraping reliability remains an active area of development.

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Pydantic
- Alembic

### Frontend

- Jinja2
- HTML5
- CSS3
- JavaScript

### Automation

- APScheduler

### Web Scraping

- Requests
- BeautifulSoup4

### Email

- SMTP
- Gmail

### Testing

- Pytest
- FastAPI TestClient
- SQLite in-memory test database

### Deployment

- Railway
- Uvicorn
- PostgreSQL
- Alembic migrations

---

## Project Architecture

```text
price-tracker-saas/
│
├── alembic/
│   └── versions/
│
├── app/
│   │
│   ├── api/
│   │   ├── api_auth.py
│   │   ├── api_products.py
│   │   ├── api_tracker.py
│   │   └── server.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── emailer.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── price_history.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── price_history.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── scheduler/
│   │   │   └── scheduler.py
│   │   │
│   │   ├── scrapers/
│   │   │   ├── amazon.py
│   │   │   ├── base.py
│   │   │   ├── bestbuy.py
│   │   │   ├── ebay.py
│   │   │   ├── target.py
│   │   │   └── walmart.py
│   │   │
│   │   ├── tracking/
│   │   │   ├── models.py
│   │   │   └── tracker.py
│   │   │
│   │   ├── dashboard.py
│   │   ├── product_stats.py
│   │   ├── product_validation.py
│   │   └── scraper.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── components.css
│   │   │   ├── layout.css
│   │   │   ├── pages.css
│   │   │   └── variables.css
│   │   │
│   │   └── js/
│   │       └── dashboard.js
│   │
│   ├── templates/
│   │   ├── email/
│   │   ├── errors/
│   │   ├── add_product.html
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── edit_product.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── product_detail.html
│   │   ├── products.html
│   │   ├── register.html
│   │   └── settings.html
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
├── scripts/
│   └── seed.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_product_validation.py
│   ├── test_products.py
│   └── test_tracker.py
│
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── run.py
└── README.md
```

---

## Application Flow

A manual or scheduled product check follows approximately this path:

```text
Tracked Product
      │
      ▼
Tracking Service
      │
      ▼
Scraper Dispatcher
      │
      ▼
Retailer Scraper
      │
      ├── Price
      ├── Availability
      └── Scrape Status
      │
      ▼
Tracking Result
      │
      ├── Update Product
      ├── Store Price History
      ├── Evaluate Target Price
      └── Evaluate Stock Transition
      │
      ▼
PostgreSQL
      │
      ▼
Email Alert
(if conditions are met)
```

The scraper layer and tracking layer are intentionally separated.

A retailer scraper is responsible for determining what the retailer page contains.

The tracking service is responsible for deciding what the application should do with that information.

---

## Database

MAG PriceWatch uses **PostgreSQL** in production and **SQLAlchemy 2** as its ORM.

The primary application models include:

### User

Stores account information such as:

- Name
- Email
- Password hash
- Timezone

### TrackedProduct

Stores information including:

- Product owner
- Product name
- Product URL
- Target price
- Current price
- Stock state
- Last checked time
- Price alert state
- Stock alert state

### PriceHistory

Stores individual successful price observations associated with tracked products.

---

## Database Migrations

Database schema changes are managed with **Alembic**.

The current migration history includes:

```text
Initial schema
      ↓
Alert tracking fields
      ↓
Stock tracking fields
      ↓
User timezone
```

Apply all migrations:

```bash
alembic upgrade head
```

Check the currently applied revision:

```bash
alembic current
```

View migration history:

```bash
alembic history
```

---

## API

MAG PriceWatch includes versioned FastAPI routes under:

```text
/api/v1
```

The API architecture currently contains routers for:

- Authentication
- Products
- Product tracking

FastAPI also provides automatically generated interactive API documentation.

When the application is running, Swagger UI is available at:

```text
/docs
```

and the OpenAPI schema is available at:

```text
/openapi.json
```

---

## Running Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd price-tracker-saas
```

---

### 2. Create a Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

Install production dependencies:

```bash
pip install -r requirements.txt
```

For development and testing:

```bash
pip install -r requirements-dev.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key

GMAIL_USER=your_email
GMAIL_PASSWORD=your_app_password

HTTPS_ONLY=False
```

Production credentials should never be committed to source control.

The `.env` file is excluded through `.gitignore`.

---

### 5. Configure the Database

Run:

```bash
alembic upgrade head
```

This brings the configured database to the latest schema revision.

---

### 6. Start the Application

For local development:

```bash
uvicorn app.api.server:app --reload
```

The application will normally be available at:

```text
http://127.0.0.1:8000
```

---

## Testing

MAG PriceWatch includes an automated Pytest suite covering major application behavior.

Current test areas include:

- Authentication
- Product validation
- Product operations
- Product tracking

Run the complete suite:

```bash
pytest -v
```

Current test status:

```text
26 passed
```

Tests use an isolated in-memory SQLite database through SQLAlchemy's `StaticPool`, preventing the automated test suite from modifying the production PostgreSQL database.

---

## Production Deployment

MAG PriceWatch is deployed on **Railway**.

The production architecture is approximately:

```text
                    Internet
                       │
                     HTTPS
                       │
                       ▼
                 Railway Proxy
                       │
                       ▼
                Uvicorn / FastAPI
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      Web Application        APScheduler
            │                     │
            └──────────┬──────────┘
                       │
                       ▼
                   SQLAlchemy
                       │
                       ▼
             Railway PostgreSQL
```

The application listens on Railway's dynamically assigned port:

```bash
uvicorn app.api.server:app --host 0.0.0.0 --port $PORT
```

Production database migrations are handled through Alembic.

Production secrets and database credentials are supplied through environment variables rather than being committed to the repository.

---

## Security

MAG PriceWatch includes several application security practices:

- Password hashing
- Session-based authentication
- User-scoped product access
- Environment-based secrets
- HTTPS-only session cookies in production
- SameSite cookie protection
- Protected product operations
- SQLAlchemy parameterized database operations
- Transaction rollback on database failures
- Custom production error handling
- Sensitive credentials excluded from Git

The following values should never be committed:

```text
DATABASE_URL
SECRET_KEY
GMAIL_PASSWORD
.env
```

---

## Error Handling

The application includes custom handling for common web errors, including:

```text
404 Not Found
500 Internal Server Error
```

The scraper architecture also distinguishes between several different product states.

For example, an unavailable product is not necessarily considered a failed scrape:

```text
Successful scrape
Price: None
Availability: Out of Stock
```

This is different from:

```text
Failed scrape
Price: Unknown
Availability: Unknown
```

This distinction allows the tracking service to make better decisions about price history and stock alerts.

---

## Background Scheduling

The application's scheduler is integrated into the FastAPI application lifecycle.

When the application starts:

```text
FastAPI Startup
      │
      ▼
Start APScheduler
```

When the application shuts down:

```text
FastAPI Shutdown
      │
      ▼
Stop APScheduler
```

Scheduled product checks use the same core tracking service as manual checks, reducing duplicated business logic between automated and user-triggered operations.

---

## Development Status

MAG PriceWatch is actively being developed.

### Implemented

- FastAPI backend
- PostgreSQL persistence
- SQLAlchemy ORM
- Alembic migrations
- User registration
- User authentication
- Session management
- Password changes
- User-specific products
- Product creation
- Product editing
- Product deletion
- Manual product checks
- Price history
- Product analytics
- Stock state tracking
- Price alert logic
- Back-in-stock alert logic
- Email notifications
- Background scheduler
- Automated test suite
- Production deployment
- HTTPS production configuration
- Custom error pages

### In Progress

- Production Amazon scraping reliability
- Expanded retailer support
- Scraper diagnostics
- Additional automated test coverage
- Production monitoring and observability

---

## Lessons & Engineering Goals

This project began as a relatively small Python price-alert exercise and evolved into a larger software engineering project.

The goal became building the infrastructure around the scraper rather than simply extracting a price from a webpage.

Development has included hands-on work with:

- FastAPI application architecture
- REST API design
- Server-side rendered web applications
- Authentication
- Authorization
- Relational database design
- SQLAlchemy ORM
- PostgreSQL
- Database migrations
- Background jobs
- Web scraping
- Email automation
- Application state
- Price-history modeling
- Error handling
- Automated testing
- Environment configuration
- Git workflows
- Cloud deployment
- Production debugging

One of the major engineering lessons from the project has been the difference between code that works locally and software that operates reliably in a production environment.

---

## Roadmap

Future improvements may include:

- Expanded retailer support
- More resilient production scraping
- Additional price-history visualizations
- Improved product analytics
- Better retry and failure handling
- Additional API coverage
- Increased automated test coverage
- Production health monitoring
- Scheduler observability
- User notification preferences
- Additional alert types

---

## Author

**Zach Magliaro**

Python / Backend Software Developer

GitHub: `magliarozach-phntm`

---

## Disclaimer

MAG PriceWatch is an educational and portfolio software project.

Retailer websites may change their markup, availability rules, pricing presentation, or automated-access restrictions at any time. These changes can affect price-check reliability.

Pricing and availability returned by MAG PriceWatch should be verified directly with the retailer before making a purchasing decision.
