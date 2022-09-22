from aiohttp import ClientResponse

from modules.base_api import BaseAPI

from .models import User


class UsersAPI(BaseAPI):
    async def get_user(self, user_id: int) -> User | None:
        response = await self.get(f"/api/users/{user_id}")
        if response.status == 404:
            return None

        json_response = await response.json()
        return User.model_validate(json_response)

    async def create_user(self, user_id: int):
        params = {
            "user_id": user_id,
        }
        response: ClientResponse = await self.post("/api/users/", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True

    async def register_moodle(self, user_id: int, mail: str, api_token: str, moodle_id: int):
        params = {
            "mail": mail,
            "api_token": api_token,
            "moodle_id": moodle_id,
        }
        response: ClientResponse = await self.post(f"/api/users/{user_id}/register_moodle/", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True

    async def set_moodle_id(self, user_id: int, moodle_id: int):
        params = {
            "moodle_id": moodle_id,
        }
        response: ClientResponse = await self.post(f"/api/users/{user_id}/set_moodle_id/", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True

    async def set_active(self, user_id: int):
        response: ClientResponse = await self.post(f"/api/users/{user_id}/set_active/")
        json_response = await response.json()
        assert json_response.get("success") is True
