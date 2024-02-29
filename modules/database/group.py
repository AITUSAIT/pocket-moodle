from modules.database.db import DB
from modules.database.models import Group


class GroupDB(DB):
    @classmethod
    async def add_group(cls, group_tg_id: int, group_name: str) -> None:
        async with cls.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO users_groups (group_tg_id, group_name) VALUES ($1, $2);", group_tg_id, group_name
            )

    @classmethod
    async def register(cls, user_id: int, group_id: int) -> None:
        async with cls.pool.acquire() as connection:
            await connection.execute("INSERT INTO user_to_group (user_id, group_id) VALUES ($1, $2);", user_id, group_id)

    @classmethod
    async def get_group(cls, group_tg_id: int) -> Group | None:
        async with cls.pool.acquire() as connection:
            rows = await connection.fetch(
                """SELECT
                    ug.id AS group_id,
                    ug.group_tg_id,
                    ug.group_name,
                    utg.user_id
                FROM
                    users_groups ug
                JOIN
                    user_to_group utg ON ug.id = utg.group_id
                WHERE
                    ug.group_tg_id = $1;""",
                group_tg_id,
            )
            if rows == [] or rows is None:
                rows = await connection.fetchrow(
                    """SELECT
                    id,
                    group_tg_id,
                    group_name
                FROM
                    users_groups
                WHERE
                    group_tg_id = $1;""",
                    group_tg_id,
                )
                if rows is None:
                    return None

                return Group(id=rows["id"], tg_id=rows["group_tg_id"], name=rows["group_name"], users=[])

            users = [row["user_id"] for row in rows]
            return Group(id=rows[0]["group_id"], tg_id=rows[0]["group_tg_id"], name=rows[0]["group_name"], users=users)
