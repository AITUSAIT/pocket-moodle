from modules.base_api import BaseAPI

from .models import CourseContent, CourseContentModule, CourseContentModuleFile, CourseContentModuleUrl


class CourseContentsAPI(BaseAPI):
    async def get_course_contents(self, course_id: int) -> dict[str, CourseContent]:
        response = await self.get(f"/api/course_contents/{course_id}/")

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
        return {}
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
