from . import UserDB
from .models import Transaction


class PaymentDB(UserDB):
    @classmethod
    async def create_payment(cls, transaction: Transaction) -> None:
        async with cls.pool.acquire() as connection:
            await connection.execute(
                'INSERT INTO user_payment (result, message, trackId, payLink, cost, months, user_id, message_id, user_mail, is_for_promocode, verified) '
                'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)',
                transaction['result'], transaction['message'], transaction['trackId'],
                transaction['payLink'], transaction['cost'], transaction['months'],
                transaction['user_id'], transaction['message_id'], transaction['user_mail'],
                transaction['is_for_promocode'], False
            )

    @classmethod
    async def delete_payment(cls, trackId: int) -> None:
        async with cls.pool.acquire() as connection:
            await connection.execute('DELETE FROM user_payment WHERE trackId = $1', trackId)

    @classmethod
    async def get_payments(cls, user_id: int) -> Transaction:
        async with cls.pool.acquire() as connection:
            _ = await connection.fetchall('SELECT * FROM user_payment WHERE user_id = $1', user_id)
            payment = {
                'result': _[1],
                'message': _[2],
                'trackId': _[3],
                'payLink': _[4],
                'cost': _[5],
                'months': _[6],
                'user_id': _[7],
                'message_id': _[8],
                'user_mail': _[9],
                'is_for_promocode': _[10]
            }
            return Transaction(payment)
        
    @classmethod
    async def get_payment_by_track_id(cls, track_id: int) -> Transaction:
        async with cls.pool.acquire() as connection:
            _ = await connection.fetchrow('SELECT * FROM user_payment WHERE trackId = $1', track_id)
            payment = {
                'result': _[1],
                'message': _[2],
                'trackId': _[3],
                'payLink': _[4],
                'cost': _[5],
                'months': _[6],
                'user_id': _[7],
                'message_id': _[8],
                'user_mail': _[9],
                'is_for_promocode': _[10]
            }
            return Transaction(payment)
        
    @classmethod
    async def update_payment(cls, transaction: Transaction) -> None:
        async with cls.pool.acquire() as connection:
            await connection.execute(
                'UPDATE user_payment SET verified = $1 WHERE trackId = $2;',
                True, transaction['trackId']
            )
    