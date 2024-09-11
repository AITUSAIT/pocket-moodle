from aiohttp import ClientResponse
from dacite import from_dict

from modules.base_api import BaseAPI

from .models import NotificationStatus


class NotificationsAPI(BaseAPI):
    async def get_notification_status(self, user_id: int) -> NotificationStatus:
        response = await self.get(f"/api/notifications/{user_id}")
        json_response = await response.json()
        return from_dict(NotificationStatus, json_response)

    async def set_notification_status(self, user_id: int, notification_status: NotificationStatus):
        params = {
            "notification_status": notification_status.to_dict(),
        }
        response: ClientResponse = await self.post(f"/api/notifications/{user_id}", params=params)
        json_response = await response.json()
        assert json_response.get("success") is True
