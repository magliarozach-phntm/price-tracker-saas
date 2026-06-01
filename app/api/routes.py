from fastapi import APIRouter
from app.services.tracker import check_product

router = APIRouter()

# Temporary in-memory storage (we’ll improve later)
products = []

@router.get("/")
def home():
    return {"status": "running"}

@router.post("/products")
def add_product(product: dict):
    """
    product = {
        name,
        url,
        target_price
    }
    """
    products.append(product)
    return {"message": "Product added", "product": product}

@router.get("/products")
def list_products():
    return products

@router.post("/check")
def check_all():
    results = []

    for p in products:
        result = check_product(p)
        results.append(result)

    return results

@router.delete("/products/{product_name}")
def delete_product(product_name: str):
    global products

    products = [
        p for p in products
        if p["name"] != product_name
    ]

    return {
        "message": f"{product_name} removed"
    }

@router.delete("/products")
def clear_products():
    products.clear()

    return {
        "message": "All products removed"
    }