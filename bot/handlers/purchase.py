from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from bot.objects.logger import print_msg
from bot.keyboards.default import main_menu
from bot.keyboards.moodle import register_moodle_query
from bot.objects import aioredis


@print_msg
async def demo_query(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
        await aioredis.activate_demo(user_id)
        if await aioredis.is_registered_moodle(user_id):
            text = "You have activated 1 month subscription!"
            kb = main_menu()
        else:
            text = "You have activated 1 month subscription!\n\n" \
                "Now you need register your Moodle account"
            kb = main_menu(register_moodle_query())
                        
    else:
        if await aioredis.is_activaited_demo(user_id):
            text = "You already have activaited demo"
            kb = main_menu()
        else:
            await aioredis.activate_demo(user_id)
            if await aioredis.is_registered_moodle(user_id):
                text = "You have activated 1 month subscription!"
                kb = main_menu()
            else:
                text = "You have activated 1 month subscription!\n\n" \
                    "Now you need register your Moodle account"
                kb = main_menu(register_moodle_query())

    await query.message.edit_text(text, reply_markup=kb)


@print_msg
async def demo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)
        await aioredis.activate_demo(user_id)
        if await aioredis.is_registered_moodle(user_id):
            text = "You have activated 1 month subscription!"
            kb = main_menu()
        else:
            text = "You have activated 1 month subscription!\n\n" \
                "Now you need register your Moodle account"
            kb = main_menu(register_moodle_query())

    else:
        if await aioredis.is_activaited_demo(user_id):
            text = "You already have activaited demo"
            kb = main_menu()
        else:
            if await aioredis.is_registered_moodle(user_id):
                text = "You have activated 1 month subscription!"
                kb = main_menu()
            else:
                text = "You have activated 1 month subscription!\n\n" \
                    "Now you need register your Moodle account"
                kb = main_menu(register_moodle_query())
                
    await message.answer(text, reply_markup=kb)
        

@print_msg
async def purchase(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    user_id = query.from_user.id

    if await aioredis.if_user(user_id):
        await aioredis.new_user(user_id)

    await query.message.delete()


def register_handlers_purchase(dp: Dispatcher):
    dp.register_message_handler(demo, commands="demo", state="*")

    dp.register_callback_query_handler(
        demo_query,
        lambda c: c.data == "demo",
        state="*"
    )
    dp.register_callback_query_handler(
        purchase,
        lambda c: c.data == "purchase",
        state="*"
    )
