import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_price(url: str) -> float:
    print(f"Checking {url}...")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    print("Request completed")

    soup = BeautifulSoup(response.content, "html.parser")
    price_element = soup.find(class_="a-offscreen")

    if price_element is None:
        raise ValueError("Price element not found on page")

    price_text = price_element.get_text().strip()
    return float(price_text.replace("$", "").replace(",", ""))