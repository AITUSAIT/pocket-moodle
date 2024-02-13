import os

import dotenv

dotenv.load_dotenv()


SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

TOKEN = os.getenv("TOKEN")
TOKEN_NOTIFY = os.getenv("TOKEN_notify")

RATE = 1

TEST = bool(int(os.getenv("TEST", "0")))

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
