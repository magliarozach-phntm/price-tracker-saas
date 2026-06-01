# 🛒 Price Tracker SaaS (FastAPI Backend)

A backend system that tracks e-commerce product prices, stores historical data, and sends email alerts when prices drop below a target price.

---

## 🚀 Features

- Web scraping Amazon product prices
- Multi-product tracking
- SQLite database for price history
- Email alerts (SMTP Gmail)
- FastAPI REST API
- Swagger API documentation

---

## 🛠 Tech Stack

- Python
- FastAPI
- SQLite
- Requests
- BeautifulSoup
- SMTP

---

## 📡 API Endpoints

### GET /
Health check

### POST /products
Add a product to track

### GET /products
List all products

### POST /check
Manually run price check

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt