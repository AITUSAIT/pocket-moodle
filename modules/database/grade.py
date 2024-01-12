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

    @classmethod
    async def set_grade(cls, user_id: int, course_id: int, grade_id: int, name: str, percentage: str):
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            await connection.execute(f'INSERT INTO grades (course_id, grade_id, user_id, name, percentage) VALUES ($1, $2, $3, $4, $5)', course_id, grade_id, user.user_id, name, percentage)
    
    @classmethod
    async def update_grade(cls, user_id: int, course_id: int, grade_id: int, percentage: str):
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            await connection.execute(f'UPDATE grades SET percentage = $1 WHERE course_id = $2, grade_id = $3, user_id = $4', percentage, course_id, grade_id, user.user_id)
    
    