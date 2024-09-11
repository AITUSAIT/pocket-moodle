from config import PM_HOST
from modules.pm_api.courses import CoursesAPI
from modules.pm_api.groups import GroupsAPI
from modules.pm_api.notifications import NotificationsAPI
from modules.pm_api.queue import QueueAPI
from modules.pm_api.users import UsersAPI


class PocketMoodleAPI(UsersAPI, GroupsAPI, CoursesAPI, NotificationsAPI, QueueAPI):
    host = PM_HOST
