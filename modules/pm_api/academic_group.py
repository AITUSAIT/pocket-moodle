import aiohttp
from aiohttp import ClientResponse

from config import PM_HOST
from modules.base_api import BaseAPI

from .models import AcademicGroup


class AcademicGroupAPI(BaseAPI):
    host = PM_HOST
    timeout = aiohttp.ClientTimeout(100.0)

    async def get_registered_chat_ids(self) -> list[int]:
        response = await self.get(f"/api/academic_groups/get_registered_chat_ids")
        json_response = await response.json()
        return json_response["success"]

    async def get_academic_group(self, group_name: str) -> AcademicGroup:
        response = await self.get(f"/api/academic_groups/{group_name}")
        json_response = await response.json()
        return AcademicGroup.model_validate_json(json_response)

    async def create_academic_group(self, group_name: str, educational_programm_id: int, application_year: int):
        params = {
            "group_name": group_name,
            "educational_programm_id": educational_programm_id,
            "application_year": application_year,
        }
        response: ClientResponse = await self.post("/api/academic_groups", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True

    async def register_group_head(self, group_name: str, group_head_tg_id: int):
        params = {
            "group_head_tg_id": group_head_tg_id,
        }
        response: ClientResponse = await self.post(
            f"/api/academic_groups/{group_name}/register_head_group", params=params
        )
        json_response = await response.json()
        assert json_response.get("success") is True

    async def register_group(self, group_name: str, group_tg_id: int):
        params = {
            "group_tg_id": group_tg_id,
        }
        response: ClientResponse = await self.post(f"/api/academic_groups/{group_name}/register_group", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True
