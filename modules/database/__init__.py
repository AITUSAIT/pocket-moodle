from . import models
from .db import DB
from .user import UserDB
from .group import GroupDB
from .deadline import DeadlineDB 
from .grade import GradeDB 
from .course import CourseDB
from .notification import NotificationDB
from .payment import PaymentDB
from .server import ServerDB
from .settings_bot import SettingsBotDB
from .promocode import PromocodeDB

__all__ = [
    'DB',
    'UserDB',
    'GroupDB',
    'CourseDB',
    'GradeDB',
    'DeadlineDB',
    'NotificationDB',
    'SettingsBotDB',
    'ServerDB',
    'PaymentDB',
    'PromocodeDB',
    'models',
]


