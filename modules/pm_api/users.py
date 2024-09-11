from aiohttp import ClientResponse
from dacite import from_dict

from modules.base_api import BaseAPI

from .models import User


class UsersAPI(BaseAPI):
    async def get_user(self, user_id: int) -> User:
        response = await self.get(f"/api/users/{user_id}")
        json_response = await response.json()
        return from_dict(User, json_response)

    async def create_user(self, user_id: int):
        params = {
            "user_id": user_id,
        }
        response: ClientResponse = await self.post("/api/users", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True

    async def register_moodle(self, user_id: int, mail: str, api_token: str):
        params = {
            "user_id": user_id,
            "mail": mail,
            "api_token": api_token,
        }
        response: ClientResponse = await self.post(f"/api/users/{user_id}/register_moodle", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True
