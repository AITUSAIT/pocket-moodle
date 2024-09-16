import json
from typing import Any, BinaryIO

import aiohttp

from modules.moodle import exceptions


class MoodleAPI:
    host = "https://moodle.astanait.edu.kz"
    timeout = aiohttp.ClientTimeout(total=10)

    @classmethod
    async def get(
        cls,
        function,
        token,
        params=None,
        data=None,
        headers=None,
        host="https://moodle.astanait.edu.kz",
        end_point="/webservice/rest/server.php/",
    ) -> dict[str, Any]:
        args = {"moodlewsrestformat": "json", "wstoken": token, "wsfunction": function}
        if params:
            args.update(params)

        async with aiohttp.ClientSession(host, timeout=cls.timeout, headers=headers) as session:
            r = await session.get(end_point, params=args, data=data)
            return await r.json()

    @classmethod
    async def get_users_by_field(cls, field, value, token):
        f = "core_user_get_users_by_field"
        params = {"field": field, "values[0]": value}
        return await cls.get(function=f, token=token, params=params)

    @classmethod
    async def upload_file(cls, file: BinaryIO, file_name: str, token: str):
        data = aiohttp.FormData()
        data.add_field("filecontent", file, filename=file_name, content_type="multipart/form-data")

        args = {
            "moodlewsrestformat": "json",
            "wstoken": token,
            "token": token,
            "wsfunction": "core_files_upload",
            "filearea": "draft",
            "itemid": 0,
            "filepath": "/",
        }

        async with aiohttp.ClientSession(cls.host, timeout=cls.timeout) as session:
            async with session.post("/webservice/upload.php", params=args, data=data) as res:
                response = json.loads(await res.text())
                return response

    @classmethod
    async def save_submission(cls, token: str, assign_id: int, item_id: int | None = None, text: str | None = None):
        args = {
            "moodlewsrestformat": "json",
            "wstoken": token,
            "wsfunction": "mod_assign_save_submission",
            "assignmentid": assign_id,
        }
        if item_id:
            args["plugindata[files_filemanager]"] = item_id
        if text:
            args["plugindata[onlinetext_editor][itemid]"] = 0
            args["plugindata[onlinetext_editor][format]"] = 0
            args["plugindata[onlinetext_editor][text]"] = text

        async with aiohttp.ClientSession(cls.host, timeout=cls.timeout) as session:
            async with session.post("/webservice/rest/server.php", params=args) as res:
                response = json.loads(await res.text())
                return response

    @classmethod
    async def check_api_token(cls, mail: str, token: str):
        result: list | dict = await cls.get_users_by_field("email", mail, token)

        if not isinstance(result, list):
            if result.get("errorcode") == "invalidtoken":
                raise exceptions.WrongToken
            if result.get("errorcode") == "invalidparameter":
                raise exceptions.WrongMail

        if len(result) != 1:
            raise exceptions.WrongMail

        return result
