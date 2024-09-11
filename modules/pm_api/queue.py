from aiohttp import ClientResponse

from modules.base_api import BaseAPI


class QueueAPI(BaseAPI):
    async def insert_user(self, user_id: int):
        params = {
            "user_id": user_id,
        }
        response: ClientResponse = await self.post("/api/queue/insert", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True
