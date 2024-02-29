import json

from async_lru import alru_cache

from modules.database.db import DB
from modules.database.models import Deadline


class DeadlineDB(DB):
    @classmethod
    @alru_cache(ttl=5)
    async def get_deadlines(cls, user_id, course_id: int) -> dict[str, Deadline]:
        async with cls.pool.acquire() as connection:
            deadlines = await connection.fetch(
                """
            SELECT
                d.id, d.assign_id, d.name, d.due, dp.graded, dp.submitted, dp.status
            FROM
                deadlines d
            INNER JOIN
                deadlines_user_pair dp ON dp.id = d.id
            WHERE
                dp.user_id = $1 and d.course_id = $2
            """,
                user_id,
                course_id,
            )

            return {
                str(_[0]): Deadline(
                    id=_[0], assign_id=_[1], name=_[2], due=_[3], graded=_[4], submitted=_[5], status=json.loads(_[6])
                )
                for _ in deadlines
            }
