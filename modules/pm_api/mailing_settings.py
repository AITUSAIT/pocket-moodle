import aiohttp

from config import PM_HOST
from modules.base_api.base import BaseAPI
from modules.pm_api.models import MailingSettings


class MailingSettingsAPI(BaseAPI):
    host = PM_HOST
    timeout = aiohttp.ClientTimeout(100.0)

    async def set_settings(self, settings_id: int, settings: MailingSettings):
        response = await self.post(f"/api/mailing_settings/{settings_id}", json=settings.to_dict())
        json_response = await response.json()
        assert json_response.get("success") is True
