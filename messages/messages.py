from aiogram.types import ReplyKeyboardMarkup

msgs = {
    "hello": "Здравствуйте! Пройдите, пожалуйста, регистрацию. Введите номер телефона",
    "registered": "Вы уже зарегестрированы. Можете войти или удалить аккаунт",
    "enter_ok": "Вы успешно вошли!",
    "phone_ok": "Номер успешно принят. Пожалуйста, введите email",
    "phone_bad": "Номер не распознан, пожалуйста, повторите",
    "email_ok": "email принят, пожалйства, введите адресс",
    "email_bad": "email не распознан, повторите, пожалуйста, ввод",
    "address_ok": "Адресс принят, спасибо",
    "address_bad": "Адресс не распознан, повторите, пожалуйста, ввод",
    "pizza_show": "Название: {name}\nОписание: {desc}\nСтоимость: {price}",
    "order_get_count": "Вы хотите заказать пиццу {name}. Выберите количество или напишите нам его",
    "order_get_address": "Ваш адрес по умолчанию: {address}. Подтвердите его использование или введите новый"
}

main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add("Вывести список пицц")
main_keyboard.insert("Сделать заказ")