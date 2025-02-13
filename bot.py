import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import save_response, save_to_google_sheets, create_db

import os
from dotenv import load_dotenv


# Завантажуємо змінні середовища з .env
load_dotenv()

# Вставте свій API токен Telegram-бота
TOKEN = os.getenv("TOKEN")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()



# Увімкнення логування
logging.basicConfig(level=logging.INFO)

# Створюємо базу даних перед запуском
create_db()

def create_inline_keyboard(options, callback_prefix):
    """Створює inline-клавіатуру з варіантами відповідей"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option, callback_data=f"{callback_prefix}:{option}")]
            for option in options
        ]
    )
    return keyboard

# 📌 **Питання для опитування**
questions = [
    ("full_name", "Ваше ім'я та прізвище?"),
    ("reason", "Чому ви вирішили вивчати англійську саме зараз?"),
    ("obstacle", "Що для вас є найбільшою перешкодою у вивченні англійської?"),
    ("future_use", "Як ви плануєте використовувати свої знання англійської мови в майбутньому?"),
    ("interest", "Які аспекти англійської мови вас цікавлять найбільше?", 
        create_inline_keyboard(["Граматика", "Розмовна мова", "Бізнес-англійська", "Підготовка до іспитів"], "interest")),
    ("format", "Який формат навчання вам більше підходить?", 
        create_inline_keyboard(["Індивідуальні заняття", "Групові заняття", "Заняття в парі"], "format")),
    ("pace", "Який темп навчання для вас найбільш комфортний?", 
        create_inline_keyboard(["1 раз на тиждень", "2 рази на тиждень", "3 рази на тиждень", "Мікро-навчання"], "pace")),
    ("hobbies", "Які у вас хобі та інтереси?"),
    ("daily_use", "Як часто ви використовуєте англійську мову в повсякденному житті?"),
    ("favorites", "Які ваші улюблені фільми, книги, музика англійською мовою?")
]

# Словник для збереження стану користувачів
user_states = {}

@dp.message(Command("start"))
async def start_survey(message: types.Message):
    """Обробляє команду /start і запускає опитування"""
    user_id = message.from_user.id
    user_states[user_id] = 0  # Починаємо з першого питання
    await message.answer("Привіт! Давай почнемо опитування. Відповідай на питання.")
    await ask_question(user_id, message)

async def ask_question(user_id, message):
    """Надсилає наступне питання користувачеві"""
    index = user_states[user_id]
    if index < len(questions):
        question = questions[index]
        column = question[0]
        text = question[1]
        keyboard = question[2] if len(question) > 2 else None  # Використовуємо клавіатуру, якщо вона є

        if keyboard:
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(text)
    else:
        await message.answer("Дякую за ваші відповіді! Ми збережемо вашу інформацію.")
        save_to_google_sheets(user_id)  # Зберігаємо в Google Sheets
        del user_states[user_id]  # Видаляємо користувача зі списку опитування

@dp.message()
async def handle_response(message: types.Message):
    """Обробляє відповіді користувача та переходить до наступного питання"""
    user_id = message.from_user.id
    if user_id in user_states:
        index = user_states[user_id]
        column = questions[index][0]  # Визначаємо, в яку колонку записати відповідь
        save_response(user_id, column, message.text)  # Зберігаємо відповідь
        user_states[user_id] += 1  # Переходимо до наступного питання
        await ask_question(user_id, message)  # Надсилаємо наступне питання

@dp.callback_query()
async def handle_inline_response(callback_query: types.CallbackQuery):
    """Обробляє вибір користувача з inline-кнопок"""
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    column, answer = data[0], data[1]  # Витягуємо колонку і відповідь
    
    if user_id in user_states:
        index = user_states[user_id]
        expected_column = questions[index][0]

        if column == expected_column:  # Переконуємося, що це правильне питання
            save_response(user_id, column, answer)  # Зберігаємо відповідь
            user_states[user_id] += 1  # Переходимо до наступного питання
            await callback_query.message.edit_text(f"✅ Ваша відповідь: {answer}")  # Оновлюємо повідомлення
            await ask_question(user_id, callback_query.message)  # Надсилаємо наступне питання

    await callback_query.answer()  # Закриваємо повідомлення про натискання кнопки

async def main():
    """Головна асинхронна функція для запуску бота"""
    await dp.start_polling(bot)

# Запускаємо бота
if __name__ == "__main__":
    asyncio.run(main())
    