import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta


class UserJSONEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=arguments-renamed
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@dataclass
class User:
    user_id: int
    api_token: str
    register_date: datetime
    mail: str
    last_active: datetime | None

    def is_newbie(self) -> bool:
        register_date = self.register_date
        return datetime.now() - register_date < timedelta(days=14)

    def is_active_user(self) -> bool:
        return self.last_active is not None and self.last_active > datetime.now() - timedelta(weeks=2)

    def has_api_token(self) -> bool:
        return self.api_token is not None

    def to_json(self) -> str:
        return json.dumps(asdict(self), cls=UserJSONEncoder)

    def to_dict(self):
        return json.loads(self.to_json())

    def __hash__(self) -> int:
        return hash((self.user_id))

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False


@dataclass
class Group:
    id: int
    tg_id: int
    name: str
    users: list[int]


@dataclass
class Grade:
    grade_id: int
    name: str
    percentage: str


@dataclass
class Deadline:
    id: int
    assign_id: int
    name: str
    due: datetime
    graded: bool
    submitted: bool
    status: int


@dataclass
class Course:
    course_id: int
    name: str
    active: bool
    grades: dict[str, Grade]
    deadlines: dict[str, Deadline]


@dataclass
class NotificationStatus:
    status: bool
    is_newbie_requested: bool
    is_update_requested: bool
    is_end_date: bool
    error_check_token: bool


@dataclass
class SettingBot:
    status: bool
    notification_grade: bool
    notification_deadline: bool


@dataclass
class SettingApp:
    status: bool
    notification_grade: bool
    notification_deadline: bool


@dataclass
class Server:
    token: str
    name: str
    proxies: list


@dataclass
class CourseContent:
    id: int
    name: str
    section: int
    modules: dict[str, "CourseContentModule"]


@dataclass
class CourseContentModule:
    id: int
    url: str
    name: str
    modplural: str
    modname: str
    files: dict[str, "CourseContentModuleFile"]
    urls: dict[str, "CourseContentModuleUrl"]


@dataclass
class CourseContentModuleFile:
    id: int
    filename: str
    filesize: int
    fileurl: str
    timecreated: int
    timemodified: int
    mimetype: str
    bytes: bytes


@dataclass
class CourseContentModuleUrl:
    id: int
    name: str
    url: str
