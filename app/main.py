import logging
from aiogram import Bot, Dispatcher, types
from config import Config

#for web app and webhook
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher with storage to save states
bot = Bot(token=Config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

from app.bot import *
from app.web import *

app = web.Application()
app.add_routes([web.get('/api', api_handler)])
# every request to /bot route will be retransmitted to dispatcher to be handled
# as a bot update
configure_app(dp, app, "/bot")
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
