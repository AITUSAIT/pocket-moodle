from async_lru import alru_cache

from . import DeadlineDB 
from . import GradeDB 
from .models import Course


class CourseDB(DeadlineDB, GradeDB):
    @classmethod
    @alru_cache(ttl=5)
    async def is_ready_courses(cls, user_id: int) -> bool:
        user = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            course_count = await connection.fetchval(
                f'SELECT COUNT(*) FROM courses INNER JOIN courses_user_pair cp ON cp.user_id = $1',
                user_id
            )
            return course_count > 0 
    
    @classmethod
    @alru_cache(ttl=5)
    async def get_courses(cls, user_id: int, is_active: bool = None) -> dict[str, Course]:
        user = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            courses = await connection.fetch(f'''
            SELECT
                c.course_id, c.name, cp.active
            FROM
                courses c
            INNER JOIN
                courses_user_pair cp ON c.course_id = cp.course_id
            WHERE
                cp.user_id = $1
                AND (cp.active = $2 OR $2 IS NULL);
            ''', user_id, is_active)
            
            return { str(_[0]): Course(*_, grades=(await cls.get_grades(user_id, _[0])), deadlines=(await cls.get_deadlines(user_id, _[0]))) for _ in courses }
