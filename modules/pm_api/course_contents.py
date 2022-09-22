import io

import aiohttp
import requests

from modules.base_api import BaseAPI

from .models import CourseContent, CourseContentModule, CourseContentModuleFile, CourseContentModuleUrl


class CourseContentsAPI(BaseAPI):
    async def get_course_contents(self, course_id: int) -> dict[str, CourseContent]:
        response = await self.get(f"/api/course_contents/{course_id}/", timeout=aiohttp.ClientTimeout(40))

        json_response = await response.json()
        courses: dict[str, CourseContent] = {}
        for key, value in json_response.items():
            courses[key] = CourseContent.model_validate(value)

        return courses

    async def get_course_content_modules(self, course_id: int) -> dict[str, CourseContentModule]:
        response = await self.get(f"/api/course_contents/{course_id}/modules/")

        json_response = await response.json()
        modules: dict[str, CourseContentModule] = {}
        for key, value in json_response.items():
            modules[key] = CourseContentModule.model_validate(value)

        return modules

    async def get_course_content_module_files(
        self, course_id: int, module_id: int
    ) -> dict[str, CourseContentModuleFile]:
        response = await self.get(f"/api/course_contents/{course_id}/modules/{module_id}/files/")
        json_response = await response.json()
        files: dict[str, CourseContentModuleFile] = {}
        for key, value in json_response.items():
            files[key] = CourseContentModuleFile.model_validate(value)

        return files

    async def get_course_content_module_urls(self, course_id: int, module_id: int) -> dict[str, CourseContentModuleUrl]:
        response = await self.get(f"/api/course_contents/{course_id}/modules/{module_id}/urls/")

        json_response = await response.json()
        urls: dict[str, CourseContentModuleUrl] = {}
        for key, value in json_response.items():
            urls[key] = CourseContentModuleUrl.model_validate(value)

        return urls

    async def get_course_content_module_file_bytes(self, course_id: int, module_id: int, file_id: int) -> io.BytesIO:
        buffer = io.BytesIO()
        url = self.host + f"/api/course_contents/{course_id}/modules/{module_id}/files/{file_id}/bytes"

        response = requests.get(url, stream=True, timeout=20)

        if response.status_code != 200:
            raise Exception(  # pylint: disable=broad-exception-raised
                f"Failed to fetch file {file_id}, status: {response.status_code}"
            )

        for chunk in response.iter_content(chunk_size=1024):  # 1 KB chunks
            if chunk:  # filter out keep-alive new chunks
                buffer.write(chunk)

        buffer.seek(0)
        return buffer
