from async_lru import alru_cache

from . import UserDB
from .models import User, Deadline


class DeadlineDB(UserDB):
    @classmethod
    @alru_cache(ttl=5)
    async def get_deadlines(cls, value, course_id: int) -> dict[str, Deadline]:
        user: User = await cls.get_user(value)

        async with cls.pool.acquire() as connection:
            deadlines = await connection.fetch(f'SELECT assign_id, name, due, graded, status FROM user_deadlines WHERE user_id = $1 and course_id = $2', user.user_id, course_id)
            return { str(_[0]): Deadline(*_) for _ in deadlines }


    