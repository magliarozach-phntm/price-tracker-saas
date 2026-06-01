from app.core.scraper import get_price
from app.core.database import save_price
from app.core.emailer import send_email

def check_product(product):
    price = get_price(product["url"])

    save_price(product["name"], price)

    if price < product["target_price"]:
        send_email(product["name"], price, product["url"])

    return {
        "name": product["name"],
        "price": price,
        "target": product["target_price"],
        "alert": price < product["target_price"]
    }