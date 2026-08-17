import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]
GMAIL_SERVER = os.getenv(
    "GMAIL_SERVER",
    "smtp.gmail.com"
)