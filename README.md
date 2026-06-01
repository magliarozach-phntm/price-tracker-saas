# 🛒 Price Tracker SaaS (FastAPI Backend)

A backend system that tracks e-commerce product prices, stores historical data, and sends email alerts when prices drop below a target price.

## 🚀 Live Demo

API Status:
https://price-tracker-saas-lqca.onrender.com/

Interactive API Documentation (Swagger):
https://price-tracker-saas-lqca.onrender.com/docs

### Demo Product URL

For reliable testing, use:

https://appbrewery.github.io/instant_pot/

Note: Amazon may block requests originating from cloud-hosted environments. The App Brewery demo page is included to demonstrate scraping functionality consistently across deployments.
---

## 🚀 Features

- Web scraping product prices
- Multi-product tracking
- SQLite database for price history
- Email alerts (SMTP Gmail)
- FastAPI REST API
- Swagger API documentation
- Cloud deployment on Render

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