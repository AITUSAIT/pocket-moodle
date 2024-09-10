import dotenv
from pytz import timezone

from modules.utils.config_utils import get_from_env

dotenv.load_dotenv()


TOKEN = str(get_from_env("TOKEN"))
TOKEN_NOTIFY = str(get_from_env("TOKEN_notify"))

RATE = 1

TEST = bool(get_from_env(field="TEST", default="0", value_type=int))

DB_HOST = get_from_env("DB_HOST")
DB_PORT = get_from_env("DB_PORT")
DB_DB = get_from_env("DB_DB")
DB_USER = get_from_env("DB_USER")
DB_PASSWD = get_from_env("DB_PASSWD")

HALFTERM_MIN = 25
TERM_MIN = 50
RETAKE_MIN = 50
SCHOLARSHIP_THRESHOLD = 70
ENHANCED_SCHOLARSHIP_THRESHOLD = 90

TZ_RAW = str(get_from_env("TZ", "Asia/Aqtobe"))
TZ = timezone(TZ_RAW)
