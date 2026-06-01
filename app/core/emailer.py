import smtplib
from email.mime.text import MIMEText
from app.core.config import GMAIL_USER, GMAIL_PASS, GMAIL_SERVER

def send_email(product_name: str, price: float, url: str):
    body = f"""
{product_name} is now ${price}!

Buy here:
{url}
"""

    msg = MIMEText(body)
    msg["Subject"] = f"{product_name} Price Alert"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    with smtplib.SMTP(GMAIL_SERVER, 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)