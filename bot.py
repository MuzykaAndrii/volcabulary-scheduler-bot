import logging

from aiogram import Bot, Dispatcher, executor, types
from config import Config

from database import manage_user

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=Config.TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
@manage_user
async def send_welcome(message: types.Message):
    await message.answer("Hi! I can help to improve your vocabulary")

@dp.message_handler(commands=['create'])
@manage_user
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(row_width=3)
    keyboard.add(types.KeyboardButton('Save'))

    await message.answer("Send me word and translation in format: word -\
         translation\nTo save all words press 'Save' button in your keyboard", reply_markup=keyboard)



@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)