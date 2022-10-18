import re

from aiogram.utils import callback_data

import database
from database import UsersTable, PizzaTable, OrdersTable
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
    register_waiting_phone_state = State()
    register_waiting_email_state = State()
    register_waiting_address_state = State()


@dp.message_handler(commands=['start', 'help'], state="*")
async def send_welcome(message: types.Message):
    await StateMachine.register_waiting_phone_state.set()

    await message.reply(get_message_text("hello"))

    logging.info(f"{message.from_user.username}: {message.text}")


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
async def handle_email(message: types.Message, state: FSMContext):
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
            await message.answer(
                text=get_message_text("pizza_show",
                                      name=pizza.name,
                                      desc=pizza.desc,
                                      price=pizza.price),
                reply_markup=markup
            )
    elif message.text == "Сделать заказ":
        pass


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
