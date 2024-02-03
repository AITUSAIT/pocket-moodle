from async_lru import alru_cache

from modules.database.db import DB
from modules.database.models import Grade


class GradeDB(DB):
    @classmethod
    @alru_cache(ttl=5)
    async def get_grades(cls, user_id, course_id: int) -> dict[str, Grade]:
        async with cls.pool.acquire() as connection:
            grades = await connection.fetch(
                "SELECT grade_id, name, percentage FROM grades WHERE user_id = $1 and course_id = $2",
                user_id,
                course_id,
            )
            return {str(_[0]): Grade(*_) for _ in grades}
