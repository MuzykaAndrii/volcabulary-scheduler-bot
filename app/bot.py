# for db
from app.database import manage_user, Bundle, User, session
#for state machine
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
# importing bot instances
from app.main import storage, dp, Config
from aiogram import types

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
    current_user_id = current_user.id
    new_bundle = Bundle(current_user_id)
    new_bundle.encode_words(words)
    try:
        session.add(new_bundle)
        session.commit()
        bundle_id = new_bundle.id
        session.close()
    except Exception as e:
        await message.answer('Some problem while saving data, please try one more time(', reply_markup=types.ReplyKeyboardRemove())
        print(e)
        await state.finish()
        return

    #generate api link
    link = f'{Config.WEBHOOK}api?user={current_user_id}&bundle={bundle_id}'

    await message.answer('Words saved, api link: {}'.format(link), reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(state=Words.set_word)
async def process_set_word(message: types.Message, state: FSMContext):
    """
    Set new word
    """

    # divide and clear input text
    input_data = message.text.split('-')
    try:
        word = input_data[0].strip()
        translation = input_data[1].strip()
    except IndexError:
        await message.answer("Wrong input, u should send me words in format: 'word - translation' (without brackets). Please try one more time.")
        return
    except:
        await message.answer("Something went wrong, please try again or contact with our support")
        return

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