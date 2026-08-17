from datetime import datetime
from decimal import Decimal
from email.message import EmailMessage
import smtplib

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
)

from app.core.config import (
    GMAIL_USER,
    GMAIL_PASS,
    GMAIL_SERVER,
)


email_templates = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def send_email(
    recipient: str,
    product_name: str,
    price: Decimal,
    target_price: Decimal,
    savings: Decimal,
    url: str,
):
    msg = EmailMessage()

    msg["Subject"] = f"Price Alert: {product_name}"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient

    msg.set_content(
        f"""
MAG PriceWatch

Price Drop Detected!

{product_name}

Current Price: ${price:.2f}
Your Target: ${target_price:.2f}
Savings: ${savings:.2f}

View Product:
{url}
"""
    )

    template = email_templates.get_template(
        "email/price_alert.html"
    )

    html = template.render(
        product_name=product_name,
        price=price,
        target_price=target_price,
        savings=savings,
        url=url,
        year=datetime.now().year,
    )

    msg.add_alternative(
        html,
        subtype="html",
    )

    _send_message(msg)


def send_stock_email(
    recipient: str,
    product_name: str,
    price: Decimal | None,
    url: str,
):
    msg = EmailMessage()

    msg["Subject"] = f"Back in Stock: {product_name}"
    msg["From"] = GMAIL_USER
    msg["To"] = recipient

    if price is not None:
        price_text = f"${price:.2f}"
    else:
        price_text = "Price unavailable"

    msg.set_content(
        f"""
MAG PriceWatch

Back in Stock!

{product_name}

Current Price: {price_text}

The product you're tracking is available again.

View Product:
{url}
"""
    )

    template = email_templates.get_template(
        "email/stock_alert.html"
    )

    html = template.render(
        product_name=product_name,
        price=price,
        url=url,
        year=datetime.now().year,
    )

    msg.add_alternative(
        html,
        subtype="html",
    )

    _send_message(msg)


def _send_message(
    msg: EmailMessage,
):
    with smtplib.SMTP(
        GMAIL_SERVER,
        587,
        timeout=15,
    ) as server:
        server.starttls()

        server.login(
            GMAIL_USER,
            GMAIL_PASS,
        )

        server.send_message(msg)