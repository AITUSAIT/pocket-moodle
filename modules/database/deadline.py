from datetime import datetime
import json

from . import UserDB
from .models import User, Deadline


class DeadlineDB(UserDB):
    pending_queries_deadlines = []

    @classmethod
    async def get_deadlines(cls, user_id, course_id: int) -> dict[str, Deadline]:
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            deadlines = await connection.fetch(f'''
            SELECT
                d.id, d.assign_id, d.name, d.due, dp.graded, dp.submitted, dp.status
            FROM
                deadlines d
            INNER JOIN
                deadlines_user_pair dp ON dp.user_id = $1 
            WHERE
                dp.user_id = $1 and d.course_id = $2
            ''', user_id, course_id)

            return { str(_[0]): Deadline(
                id=_[0],
                assign_id=_[1],
                name=_[2],
                due=_[3],
                graded=_[4],
                submitted=_[5],
                status=json.loads(_[6])
            ) for _ in deadlines }
