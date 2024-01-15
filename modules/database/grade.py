from async_lru import alru_cache

from . import UserDB
from .models import Grade, User


class GradeDB(UserDB):
    @classmethod
    @alru_cache(ttl=5)
    async def get_grades(cls, user_id, course_id: int) -> dict[str, Grade]:
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            grades = await connection.fetch(f'SELECT grade_id, name, percentage FROM grades WHERE user_id = $1 and course_id = $2', user.user_id, course_id)
            return { str(_[0]): Grade(*_) for _ in grades }
    