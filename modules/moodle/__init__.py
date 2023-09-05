from typing import BinaryIO

import aiohttp

from . import exceptions


class MoodleAPI:
    session = aiohttp.ClientSession('https://moodle.astanait.edu.kz')
    timeout = aiohttp.ClientTimeout(total=10)

    @classmethod
    async def make_request(cls, function, token, params=None, data=None, headers=None, host='https://moodle.astanait.edu.kz', end_point='/webservice/rest/server.php/') -> dict:
        args = {'moodlewsrestformat': 'json', 'wstoken': token, 'wsfunction': function}
        if params:
            args.update(params)

        async with aiohttp.ClientSession(host, timeout=cls.timeout, headers=headers) as session:
            if args:
                r = await session.get(end_point, params=args, data=data)
            else:
                r = await session.get(end_point, data=data)
            return await r.json()

    @classmethod
    async def get_users_by_field(cls, field, value, token):
        f = 'core_user_get_users_by_field'
        params = {
            'field': field,
            'values[0]': value
        }
        return await cls.make_request(function=f, token=token, params=params)

    @classmethod
    async def upload_file(cls, file: BinaryIO, file_name: str, token: str):
        data = aiohttp.FormData()
        data.add_field('filecontent', file, filename=file_name, content_type='multipart/form-data')

        args = {
            'moodlewsrestformat': 'json',
            # 'wstoken': token,
            # 'wsfunction': 'core_files_upload',
            'filearea': 'draft',
            'itemid': 0,
            'filepath': '/'
        }

        return await cls.make_request(function='core_files_upload', token=token, params=args, data=data)
        # async with cls.session.post("/webservice/upload.php", params=args, data=data) as res:
        #     response = json.loads(await res.text())
        #     return response

    @classmethod
    async def save_submission(cls, token: str, assign_id: str, item_id:str = '', text: str = ''):
        args = {
            'moodlewsrestformat': 'json',
            # 'wstoken': token,
            # 'wsfunction': 'mod_assign_save_submission',
            'assignmentid': assign_id
        }
        if item_id != '':
            args['plugindata[files_filemanager]'] = item_id
        if text != '':
            args['plugindata[onlinetext_editor][itemid]'] = 0
            args['plugindata[onlinetext_editor][format]'] = 0
            args['plugindata[onlinetext_editor][text]'] = text

        return await cls.make_request(function='mod_assign_save_submission', token=token, params=args)
        # async with cls.session.post("/webservice/rest/server.php", params=args) as res:
        #     response = json.loads(await res.text())
        #     return response

    @classmethod
    async def check_api_token(cls, mail: str, token: str):
        result: list | dict  = await cls.get_users_by_field('email', mail, token)

        if type(result) is not list:
            if result.get('errorcode') == 'invalidtoken':
                raise exceptions.WrongToken
            if result.get('errorcode') == 'invalidparameter':
                raise exceptions.WrongMail
            
        if len(result) != 1:
            raise exceptions.WrongMail
