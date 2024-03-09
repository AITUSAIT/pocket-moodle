from async_lru import alru_cache

from modules.database.db import DB
from modules.database.deadline import DeadlineDB
from modules.database.grade import GradeDB
from modules.database.models import Course


class CourseDB(DB):
    @classmethod
    @alru_cache(ttl=5)
    async def is_ready_courses(cls, user_id: int) -> bool:
        async with cls.pool.acquire() as connection:
            course_count = await connection.fetchval(
                "SELECT COUNT(*) FROM courses INNER JOIN courses_user_pair cp ON cp.user_id = $1", user_id
            )
            return course_count > 0

    @classmethod
    @alru_cache(ttl=5)
    async def get_courses(cls, user_id: int, is_active: bool | None = None) -> dict[str, Course]:
        async with cls.pool.acquire() as connection:
            courses = await connection.fetch(
                """
            SELECT
                c.course_id, c.name, cp.active
            FROM
                courses c
            INNER JOIN
                courses_user_pair cp ON c.course_id = cp.course_id
            WHERE
                cp.user_id = $1
                AND (cp.active = $2 OR $2 IS NULL);
            """,
                user_id,
                is_active,
            )

            return {
                str(_[0]): Course(
                    course_id=_[0],
                    name=_[1],
                    active=_[3],
                    grades=await GradeDB.get_grades(user_id=user_id, course_id=_[0]),
                    deadlines=await DeadlineDB.get_deadlines(user_id=user_id, course_id=_[0]),
                )
                for _ in courses
            }
