from app.core.scraper import get_price
from app.core.database import save_price
from app.core.emailer import send_email

products = [
    {
        "name": "Instant Pot",
        "url": "https://www.amazon.com/dp/B075CYMYK6",
        "target_price": 100
    },
    {
        "name": "Air Fryer",
        "url": "https://www.amazon.com/dp/B0C33CHG99",
        "target_price": 80
    }
]

def check_prices():
    for product in products:
        price = get_price(product["url"])

        print(f"{product['name']} = ${price}")

        save_price(product["name"], price)

        if price < product["target_price"]:
            send_email(product["name"], price, product["url"])
            print("Email sent!")