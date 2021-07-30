# for db
from app.database import manage_user, Bundle, User, session
#for state machine
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
# importing bot instances
from app.main import storage, dp, Config, bot, logging
from aiogram import types
# for passing data through callback
from aiogram.utils.callback_data import CallbackData

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
async def save_handler(message: types.Message, state: FSMContext):
    """
    Save all sended words
    """
    #fetch saved data
    async with state.proxy() as saved_data:
        pass
    
    # build words dictionary from saved data
    words = {word:translation for word, translation in saved_data.items()}

    # store words in database
    user_telegram_id = message.chat.id
    current_user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    current_user_id = current_user.id
    new_bundle = Bundle(current_user_id)
    new_bundle.encode_words(words)
    try:
        session.add(new_bundle)
        session.commit()
        final_response = new_bundle.generate_words_string()
        bundle_id = new_bundle.id
        session.close()
    except Exception as e:
        await message.answer('Some problem while saving data, please try one more time(', reply_markup=types.ReplyKeyboardRemove())
        print(e)
        await state.finish()
        return

    #generate api link
    link = f'{Config.WEBHOOK}api?user={current_user_id}&bundle={bundle_id}'
        
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    btn_api = types.InlineKeyboardButton('API link', url=link)
    btn_schedule = types.InlineKeyboardButton('Set schedule (coming soon)', callback_data='set_schedule')
    keyboard_markup.add(btn_api)
    keyboard_markup.add(btn_schedule)

    await message.answer('Words successfully saved.', reply_markup=types.ReplyKeyboardRemove())
    await message.answer(final_response, reply_markup=keyboard_markup)
    await state.finish()

@dp.callback_query_handler(text='set_schedule')
async def set_schedule(callback_query: types.CallbackQuery):
    await callback_query.answer('Scheduler is not available yet.')

@dp.message_handler(state=Words.set_word)
async def process_set_word(message: types.Message, state: FSMContext):
    """
    Set new word
    """

    response = message.text
    rows = response.split('\n')
    rows_dictionary = dict()

    for row in rows:
        divided_row = row.split('-')
        try:
            word, translation = divided_row[0].strip(), divided_row[1].strip()
        except IndexError:
            await message.answer("Wrong inputs could be missed, please send me words in format: 'word - translation' (without brackets)")
            continue
        else:
            rows_dictionary[word] = translation

    async with state.proxy() as storage:
        for word, translation in rows_dictionary.items():
            storage[word] = translation

    await message.answer("Okay, wanna to add more? Just write it")

delete_callback = CallbackData('rm_bundle', 'action', 'bundle_id')

@dp.message_handler(commands=['my'])
@manage_user
async def get_bundles(message: types.Message):
    user_telegram_id = message.chat.id
    current_user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
    current_user_id = current_user.id
    bundles = current_user.bundles
    if bundles:
        for bundle in bundles:
            words = bundle.generate_words_string()

            link = f'{Config.WEBHOOK}api?user={current_user_id}&bundle={bundle.id}'
        
            keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
            btn_api = types.InlineKeyboardButton('API link', url=link)
            btn_schedule = types.InlineKeyboardButton('Set/unset schedule (coming soon)', callback_data='set_schedule')
            btn_delete = types.InlineKeyboardButton('Delete bundle', callback_data=delete_callback.new(bundle_id=bundle.id, action='delete_bundle'))
            keyboard_markup.row(btn_api, btn_delete)
            keyboard_markup.add(btn_schedule)

            await message.answer(words, reply_markup=keyboard_markup)

@dp.callback_query_handler(delete_callback.filter(action='delete_bundle'))
async def delete_bundle_handler(query: types.CallbackQuery, callback_data: dict):
    try:
        bundle_id = int(callback_data['bundle_id'])
    except ValueError:
        await query.answer('Bundle id should be integer')
        return

    bundle = session.query(Bundle).get(bundle_id)    
    if not bundle:
        await query.answer('Bundles not found')
        return
    
    owner = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    if bundle.creator_id != owner.id:
        await query.answer('You not owner of this bundle')
        return
    
    bundle.delete()
    await bot.delete_message(query.message.chat.id, query.message.message_id)
    await query.answer('Bundle successfully deleted')

@dp.message_handler(commands=['start', 'help'])
@manage_user
async def send_welcome(message: types.Message):
    await message.answer("Hi! I can help to improve your vocabulary")

@dp.message_handler()
@manage_user
async def echo(message: types.Message):
    await message.answer('Unknown command, check list of avaliable commands')
