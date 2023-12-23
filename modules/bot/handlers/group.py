from aiogram import Dispatcher, types

from config import dp, rate
from modules.bot.functions.deadlines import get_deadlines_local_by_days_group
from modules.bot.keyboards.group import register_self

from ...database import GroupDB, UserDB


async def start(message: types.Message):
    group_id = message.chat.id
    group = await GroupDB.get_group(group_id)
    
    if not group:
        await GroupDB.add_group(group_id, message.chat.full_name)
        text = "Hi! This group was saved and now you can register self to make groups deadlines be visible!"
        await message.reply(text, reply_markup=register_self())
        return
    
    text = "If someone wants their deadlines to be visible in this group, they need to register!"
    await message.reply(text, reply_markup=register_self())


async def register(query: types.CallbackQuery):
    group_id = query.message.chat.id
    group = await GroupDB.get_group(group_id)
    
    if not group:
        await GroupDB.add_group(group_id, query.message.chat.full_name)
        text = "Hi! This group was saved and now you can register self to make groups deadlines be visible!"
        await query.message.reply(text, reply_markup=register_self())
        return
    
    user_id = query.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        text = "First of all, you need to register personlly in the Bot!"
        await query.answer(text)
        return
    
    if user.user_id in group.users:
        text = "Already registered!"
        await query.answer(text)
        return
    
    await GroupDB.register(user_id, group_id)
    text = "Success!"
    await query.answer(text)


async def get_deadlines(message: types.Message):
    group_id = message.chat.id
    group = await GroupDB.get_group(group_id)
    
    if not group:
        await GroupDB.add_group(group_id, message.chat.full_name)
        text = "Hi! This group was saved and now you can register self to make groups deadlines be visible!"
        await message.reply(text, reply_markup=register_self())
        return
    
    text = await get_deadlines_local_by_days_group(group.users, 15)
    if not text:
        text = 'So far there are no such' 
    
    await message.reply(text, parse_mode=types.ParseMode.MARKDOWN_V2)


@dp.throttled(rate=rate)
async def ignore(message: types.Message):
    try:
        await message.answer("It's not group command!")
    except:
        ...


def register_handlers_groups(dp: Dispatcher):
    dp.register_message_handler(start, lambda msg: msg.chat.type in ["group", "supergroup"], commands='start', state="*")
    
    dp.register_callback_query_handler(
        register,
        lambda c: c.data == "register",
        lambda c: c.message.chat.type in ["group", "supergroup"],
        state="*"
    )
    
    dp.register_message_handler(get_deadlines, lambda msg: msg.chat.type in ["group", "supergroup"] and msg.is_command(), state="*")
    
    dp.register_message_handler(ignore, lambda msg: msg.chat.type in ["group", "supergroup"], lambda msg: int(msg.chat.id) not in [-1001768548002] and msg.is_command(), state="*")
