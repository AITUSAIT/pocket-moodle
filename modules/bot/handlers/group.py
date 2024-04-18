from aiogram import Router, types
from aiogram.enums import ParseMode

from config import RATE
from global_vars import dp
from modules.bot.functions.deadlines import get_deadlines_local_by_days_group
from modules.bot.keyboards.group import register_self
from modules.database import GroupDB, UserDB


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

    await GroupDB.register(user_id, group.id)
    text = "Success!"
    await query.answer(text)


async def get_deadlines(message: types.Message):
    group_id = message.chat.id
    group = await GroupDB.get_group(group_id)

    if not group:
        await GroupDB.add_group(group_id, message.chat.full_name)
        await message.reply(
            "Hi! This group was saved and now you can register self to make groups deadlines be visible!",
            reply_markup=register_self(),
        )
        return

    list_text = await get_deadlines_local_by_days_group(group.users, 15)
    if not list_text:
        list_text = ["So far there are no such"]

    for i, text in enumerate(list_text):
        if text in ["", " ", "\n", "\n\n"]:
            continue
        if i != 0:
            await message.answer(text, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.reply(text, parse_mode=ParseMode.MARKDOWN_V2)


#FIX: dp.throttled needs to be rewriten as a midleware
@dp.throttled(rate=RATE)
async def ignore(_: types.Message):
    return


def register_handlers_groups(router: Router):
    router.message.register(start, lambda msg: msg.chat.type in ["group", "supergroup"], commands="start", state="*")

    router.callback_query.register(
        register, lambda c: c.data == "register", lambda c: c.message.chat.type in ["group", "supergroup"], state="*"
    )

    router.message.register(
        get_deadlines,
        lambda msg: msg.chat.type in ["group", "supergroup"] and msg.is_command(),
        commands="get_deadlines",
        state="*",
    )

    router.message.register(
        ignore,
        lambda msg: msg.chat.type in ["group", "supergroup"],
        lambda msg: int(msg.chat.id) not in [-1001768548002] and msg.is_command(),
        state="*",
    )
