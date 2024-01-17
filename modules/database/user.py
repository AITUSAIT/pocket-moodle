from datetime import datetime, timedelta

from async_lru import alru_cache

from .db import DB
from .models import User


class UserDB(DB):
    @classmethod
    async def create_user(cls, user_id: int, api_token: str) -> None:
        user_data = (user_id, api_token, datetime.now())

        notification_data = [
            (user_id, True, True, False, False),
        ]

        settings_app_data = [
            (user_id, False, True, True),
        ]

        settings_bot_data = [
            (user_id, True, True, True),
        ]

        async with cls.pool.acquire() as connection:
            async with connection.transaction():
                await connection.executemany(
                    'INSERT INTO users (user_id, api_token, register_date) VALUES ($1, $2, $3);',
                    [user_data]
                )
                await connection.executemany(
                    'INSERT INTO user_notification (user_id, status, is_newbie_requested, is_update_requested, is_end_date) VALUES ($1, $2, $3, $4, $5);',
                    notification_data
                )
                await connection.executemany(
                    'INSERT INTO user_settings_app (user_id, status, notification_grade, notification_deadline) VALUES ($1, $2, $3, $4);',
                    settings_app_data
                )
                await connection.executemany(
                    'INSERT INTO user_settings_bot (user_id, status, notification_grade, notification_deadline) VALUES ($1, $2, $3, $4);',
                    settings_bot_data
                )

        for func in [cls.get_user]:
            func.cache_invalidate(user_id)

    @classmethod
    @alru_cache(ttl=360)
    async def get_user(cls, user_id: int) -> User:
        async with cls.pool.acquire() as connection:
            user = await connection.fetchrow(f'SELECT user_id, api_token, register_date, sub_end_date, mail, count_promo_invites, last_active FROM users WHERE user_id = $1', user_id)
            return User(*user) if user else None

    @classmethod
    async def get_users(cls) -> list[User]:
        async with cls.pool.acquire() as connection:
            users = await connection.fetch(f'SELECT user_id, api_token, register_date, sub_end_date, mail, count_promo_invites, last_active FROM users')
            return [ User(*user) for user in users ]

    @classmethod
    async def register(cls, user_id: int, mail: str, api_token: str) -> None:
        async with cls.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(f'DELETE FROM courses_user_pair WHERE user_id = $1;', user_id)
                await connection.execute(f'DELETE FROM deadlines_user_pair WHERE user_id = $1;', user_id)
                await connection.execute(f'DELETE FROM grades WHERE user_id = $1;', user_id)
                await connection.execute(f'UPDATE users SET api_token = $1, mail = $2 WHERE user_id = $3', api_token, mail, user_id)
        
        for func in [cls.get_user]:
            func.cache_invalidate(user_id)

    @classmethod
    async def add_count_promo_invite(cls, user_id: int) -> User:
        async with cls.pool.acquire() as connection:
            await connection.execute(f'UPDATE users SET count_promo_invites = count_promo_invites + 1 WHERE user_id = $1', user_id)

        for func in [cls.get_user]:
            func.cache_invalidate(user_id)

    @classmethod
    @alru_cache(ttl=360)
    async def if_admin(cls, user_id: int) -> bool:
        async with cls.pool.acquire() as connection:
            admin_data = await connection.fetchrow('SELECT user_id, status FROM admin WHERE user_id = $1', user_id)
            return admin_data is not None and admin_data['status'] == 'admin'

    @classmethod
    @alru_cache(ttl=360)
    async def if_manager(cls, user_id: int) -> bool:
        async with cls.pool.acquire() as connection:
            manager_data = await connection.fetchrow('SELECT user_id, status FROM admin WHERE user_id = $1', user_id)
            return manager_data is not None and manager_data['status'] == 'manager'

    @classmethod
    async def if_msg_end_date(cls, user_id: int) -> bool:
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            data = await connection.fetchrow(f'SELECT is_end_date FROM user_notification WHERE user_id = $1', user.user_id)
            return data['is_end_date']

    @classmethod
    async def set_msg_end_date(cls, user_id: int, number: int) -> None:
        user: User = await cls.get_user(user_id)

        async with cls.pool.acquire() as connection:
            await connection.execute(f'UPDATE user_notification SET is_end_date = $1 WHERE user_id = $2', bool(number), user.user_id)

    @classmethod
    async def activate_sub(cls, user_id: int, days: int) -> None:
        user: User = await cls.get_user(user_id)

        if user:
            async with cls.pool.acquire() as connection:
                sub_end_date = user.sub_end_date
                new_sub_end_date = None
                if sub_end_date is None or sub_end_date < datetime.now():
                    new_sub_end_date = datetime.now() + timedelta(days=days)
                else:
                    new_sub_end_date = sub_end_date + timedelta(days=days)

                await connection.execute(
                    f'UPDATE users SET sub_end_date = $1 WHERE user_id = $2',
                    new_sub_end_date, user.user_id
                )
                await cls.set_msg_end_date(user_id, 0)
                cls.get_user.cache_invalidate(user_id)
