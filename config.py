import dotenv
from pytz import timezone

from modules.utils.config_utils import get_from_env

dotenv.load_dotenv()


TOKEN = str(get_from_env("TOKEN"))
TOKEN_NOTIFY = str(get_from_env("TOKEN_notify"))

RATE = 0.25

TEST = bool(get_from_env(field="TEST", default="0", value_type=int))

PM_HOST = str(get_from_env("PM_HOST"))
PM_TOKEN = str(get_from_env("PM_TOKEN"))

HALFTERM_MIN = 25
TERM_MIN = 50
RETAKE_MIN = 50
SCHOLARSHIP_THRESHOLD = 70
ENHANCED_SCHOLARSHIP_THRESHOLD = 90

TZ_RAW = str(get_from_env("TZ", "Asia/Aqtobe"))
TZ = timezone(TZ_RAW)
