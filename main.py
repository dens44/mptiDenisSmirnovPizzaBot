import re

from aiogram.utils import callback_data

import database
from database import UsersTable, PizzaTable, OrdersTable, FileTable
from messages import get_message_text, main_keyboard

import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from aiogram.contrib.fsm_storage.files import JSONStorage

from messages import get_message_text
from settings import API_TOKEN

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)

storage = JSONStorage("states.json")

dp = Dispatcher(bot, storage=storage)


class StateMachine(StatesGroup):
    main_state = State()
    registered_state = State()
    register_waiting_phone_state = State()
    register_waiting_email_state = State()
    register_waiting_address_state = State()
    order_waiting_count_state = State()
    order_waiting_address_state = State()


async def send_photo(message, filename, caption=None, reply_markup=None):
    file_id = FileTable.get_file_id_by_file_name(filename)
    if file_id is None:
        # upload_file
        with open(filename, 'rb') as photo:
            result = await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=reply_markup
            )
            file_id = result.photo[0].file_id
            FileTable.create(telegram_file_id=file_id, file_name=filename)
    else:
        await bot.send_photo(
            message.from_user.id,
            file_id,
            caption=caption,
            reply_markup=reply_markup
        )


@dp.message_handler(commands=['start', 'help'], state="*")
async def send_welcome(message: types.Message):
    telegram_id = message.from_user.id
    user = UsersTable.get_or_none(telegram_id=telegram_id)

    if user is None:
        await StateMachine.register_waiting_phone_state.set()
        await message.reply(get_message_text("hello"))
    else:
        await StateMachine.registered_state.set()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Войти", "Удалить аккаунт")
        await message.reply(get_message_text("registered"), reply_markup=markup)

    logging.info(f"{message.from_user.username}: {message.text}")


@dp.message_handler(state=StateMachine.registered_state)
async def handle_registered(message: types.Message, state: FSMContext):
    if message.text == "Удалить аккаунт":
        telegram_id = message.from_user.id
        UsersTable.delete_user_by_telegram_id(telegram_id=telegram_id)
        await StateMachine.register_waiting_phone_state.set()
        await message.reply(get_message_text("hello"))
    else:
        await state.finish()
        await StateMachine.main_state.set()
        await message.answer(get_message_text("enter_ok"), reply_markup=main_keyboard)


@dp.message_handler(state=StateMachine.register_waiting_phone_state)
async def handle_phone(message: types.Message, state: FSMContext):
    if re.fullmatch("[0-9]{10,}", message.text):
        async with state.proxy() as data:
            data["phone"] = message.text
        await message.reply(get_message_text("phone_ok"))
        await StateMachine.register_waiting_email_state.set()
    else:
        await message.reply(get_message_text("phone_bad"))


@dp.message_handler(state=StateMachine.register_waiting_email_state)
async def handle_email(message: types.Message, state: FSMContext):
    if re.fullmatch(".*@.*", message.text):
        async with state.proxy() as data:
            data["email"] = message.text
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add("Пропустить")
        await message.reply(get_message_text("email_ok"), reply_markup=markup)
        await StateMachine.register_waiting_address_state.set()
    else:
        await message.reply(get_message_text("email_bad"))


@dp.message_handler(state=StateMachine.register_waiting_address_state)
async def handle_address(message: types.Message, state: FSMContext):
    if message.text != "":
        async with state.proxy() as data:
            data["address"] = message.text if message.text != "Пропустить" else "Не указан"
            user_info = data
        await message.reply(get_message_text("address_ok"), reply_markup=main_keyboard)

        UsersTable.add_user(
            name=f"{message.from_user.first_name} {message.from_user.last_name}",
            telegram_id=message.from_user.id,
            phone=user_info["phone"],
            email=user_info["email"],
            address=user_info["address"]
        )

        await state.finish()
        await StateMachine.main_state.set()
    else:
        await message.reply(get_message_text("address_bad"))


@dp.message_handler(state=StateMachine.main_state)
async def main_state_handler(message: types.Message, state: FSMContext):
    if message.text == "Вывести список пицц":
        for pizza in PizzaTable.get_menu():
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Заказать", callback_data=f"order_pizza_{pizza.pizza_id}"))

            await send_photo(
                message,
                f'data/pizza_{pizza.pizza_id}.jpg',
                caption=get_message_text("pizza_show",
                                      name=pizza.name,
                                      desc=pizza.desc,
                                      price=pizza.price),
                reply_markup=markup
            )

    elif message.text == "Сделать заказ":
        pass


@dp.callback_query_handler(text_startswith="order_pizza_", state=StateMachine.main_state)
async def main_state_handler(call: types.CallbackQuery, state: FSMContext):
    pizza_id = call.data.split('_')[2]

    async with state.proxy() as data:
        data["order_pizza_id"] = pizza_id

    pizza: PizzaTable = PizzaTable.get(pizza_id=pizza_id)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    markup.add("отменить")
    markup.add("1", "2", "3", "4", "5", "10", "15")

    await call.message.answer(get_message_text("order_get_count", name=pizza.name), reply_markup=markup)
    await StateMachine.order_waiting_count_state.set()
    await call.answer()


@dp.message_handler(state=StateMachine.order_waiting_count_state)
async def order_waiting_count_handler(message: types.Message, state: FSMContext):
    if message.text == "отменить":
        await state.finish()
        await StateMachine.main_state.set()
    elif re.fullmatch("[0-9]{1,3}", message.text):
        count = int(message.text)
        async with state.proxy() as data:
            data["order_count"] = count
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("отменить", "подтвердить")
        current_address = UsersTable.get(telegram_id=message.from_user.id).address
        await message.answer(get_message_text("order_get_address", address=current_address), reply_markup=markup)
        await StateMachine.order_waiting_address_state.set()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
