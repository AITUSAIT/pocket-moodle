from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command

from modules.bot.functions.deadlines import get_deadlines_local_by_days_group
from modules.bot.keyboards.group import register_self
from modules.database import GroupDB, UserDB


async def start(message: types.Message):
    group_id = message.chat.id
    group = await GroupDB.get_group(group_id)

    if not group:
        await GroupDB.add_group(group_id, message.chat.full_name)
        text = (
            "Hi\! Group was *registered* to show all deadlines of participants\n\n"
            "*Click button below* to include your *deadlines* to this group"
        )
        await message.reply(text, reply_markup=register_self().as_markup(), parse_mode=ParseMode.MARKDOWN_V2)
        return

    text = "This group is already *registered*\!\n\n" "*Click button below* to include your *deadlines* to this group"
    await message.reply(text, reply_markup=register_self().as_markup(), parse_mode=ParseMode.MARKDOWN_V2)


async def register(query: types.CallbackQuery):
    if not query.message:
        return
    if isinstance(query.message, types.InaccessibleMessage):
        return
    if not query.data:
        return

    group_id = query.message.chat.id
    group = await GroupDB.get_group(group_id)

    if not group:
        text = (
            "Hi\! Group was *registered* to show all deadlines of participants\n\n"
            "*Click button below* to include your *deadlines* to this group"
        )
        await query.message.answer(text, reply_markup=register_self().as_markup(), parse_mode=ParseMode.MARKDOWN_V2)
        return

    user_id = query.from_user.id
    user = await UserDB.get_user(user_id)
    if not user:
        text = "First of all, you need to register personally in the Bot!"
        await query.answer(text)
        return

    if user.user_id in group.users:
        text = "Already included!"
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
        text = (
            "Hi\! Group was *registered* to show all deadlines of participants\n\n"
            "*Click button below* to include your *deadlines* to this group"
        )
        await message.reply(text, reply_markup=register_self().as_markup(), parse_mode=ParseMode.MARKDOWN_V2)
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


async def ignore(_: types.Message):
    return


def register_handlers_groups(router: Router):
    router.message.register(start, Command("start"))

    router.callback_query.register(
        register,
        F.func(lambda c: c.data == "register"),
    )

    router.message.register(
        get_deadlines,
        Command("get_deadlines"),
    )
