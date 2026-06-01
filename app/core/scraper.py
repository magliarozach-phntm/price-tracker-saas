import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_price(url: str) -> float:
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")

    price_text = soup.find(class_="a-offscreen").get_text().strip()
    return float(price_text.replace("$", ""))