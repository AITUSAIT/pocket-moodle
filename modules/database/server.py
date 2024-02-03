from modules.database.db import DB
from modules.database.models import Server


class ServerDB(DB):
    @classmethod
    async def get_servers(cls) -> dict[str, Server]:
        async with cls.pool.acquire() as connection:
            server = await connection.fetch("SELECT token, name, proxy_list FROM servers")
            return {_[0]: Server(*_) for _ in server}
