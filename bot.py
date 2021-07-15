import logging

from aiogram import Bot, Dispatcher, executor, types
from config import Config

from database import manage_user, Bundle, User, session

#for state machine
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

#for web app and webhook
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher with storage to save states
bot = Bot(token=Config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
class Words(StatesGroup):
    set_word = State()  # Will be represented in storage as 'Words:set_word'

@dp.message_handler(commands=['create'])
@manage_user
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton('Save'))
    keyboard.add(types.KeyboardButton('Cancel'))

    await Words.set_word.set()
    await message.answer("Send me word and translation in format: word -\
         translation\nTo save all words press 'Save' button in your keyboard\nto cancel press 'Cancel in keyboard'", reply_markup=keyboard)

#cancel saving
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())

# if swap this handler with next, command save will not works
@dp.message_handler(state=Words.set_word, commands='save')
@dp.message_handler(Text(equals='save', ignore_case=True), state=Words.set_word)
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Save all sended words
    """
    #fetch saved data
    async with state.proxy() as saved_data:
        pass
    
    # build words dictionary from saved data
    words = dict()
    for word, translation in saved_data.items():
        words[word] = translation


    # store words in database
    user_telegram_id = message.chat.id
    current_user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    new_bundle = Bundle(current_user.id)
    new_bundle.encode_words(words)
    try:
        new_bundle.save()
    except Exception as e:
        await message.answer('Some problem while saving data, please try one more time(', reply_markup=types.ReplyKeyboardRemove())
        print(e)
        await state.finish()
        return

    await message.answer('Words saved: ', reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(state=Words.set_word)
async def process_set_word(message: types.Message, state: FSMContext):
    """
    Set new word
    """

    # divide and clear input text
    input_data = message.text.split('-')
    word = input_data[0].strip()
    translation = input_data[1].strip()

    async with state.proxy() as data:
        data[word] = translation
    
    print(f'Setted {word} - {translation} for {message.chat.id} user')

    await message.answer("Okay, wanna to add one more? Just write it")

@dp.message_handler(commands=['start', 'help'])
@manage_user
async def send_welcome(message: types.Message):
    await message.answer("Hi! I can help to improve your vocabulary")

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)

# handle /api route
async def api_handler(request):
    print(request, end='\n\n\n')
    return web.json_response({"status": "OK"}, status=200)


app = web.Application()
# add a custom route
app.add_routes([web.get('/api', api_handler)])
# every request to /bot route will be retransmitted to dispatcher to be handled
# as a bot update
configure_app(dp, app, "/bot")

if __name__ == '__main__':
    # executor.start_polling(dp, skip_updates=True)
    web.run_app(app, port=5000)