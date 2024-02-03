import os

import dotenv

dotenv.load_dotenv()


SERVER_PORT = os.getenv("SERVER_PORT", "default=8080")

TOKEN = os.getenv("TOKEN")
TOKEN_NOTIFY = os.getenv("TOKEN_notify")

RATE = 1

TEST = bool(int(os.getenv("TEST", "0")))

OXA_MERCHANT_KEY = os.getenv("OXA_MERCHANT_KEY")
if TEST:
    OXA_MERCHANT_KEY = "sandbox"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_DB = os.getenv("DB_DB")
DB_USER = os.getenv("DB_USER")
DB_PASSWD = os.getenv("DB_PASSWD")

HALFTERM_MIN = 25
TERM_MIN = 50
RETAKE_MIN = 50
SCHOLARSHIP_THRESHOLD = 70
ENHANCED_SCHOLARSHIP_THRESHOLD = 90

prices = {
    "1": 0.75,
    "3": 2.1,
    "6": 3.9,
    "9": 5.4,
    "12": 6.6,
}
