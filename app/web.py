from app.main import bot, Config, dp, logging
from app.database import Bundle, User, session
from aiohttp import web
import json

def for_dump(words):
    return json.dumps(words, ensure_ascii=False)

async def on_startup(dp):
    logging.warning('STARTING APP...')
    await bot.set_webhook(Config.WEBHOOK + 'bot')

async def on_shutdown(dp):
    logging.warning('Shutting down...')

# handle /api route
async def api_handler(request):
    url_params = request.rel_url.query
    try:
        user_id = int(url_params['user'])
        bundle_id = int(url_params['bundle'])
    # not found needed keys
    except KeyError:
        return web.json_response({"status": "Expected args: user, bundle"}, status=404)
    # ids is not integers
    except ValueError:
        return web.json_response({"status": "Expected args types: integer"}, status=404)
        
    bundle = session.query(Bundle).filter(Bundle.id==bundle_id, Bundle.creator_id==user_id).first()
    # if bundle exists
    if bundle:
        return web.json_response(Bundle.serialize_to_pretty(bundle.decode_words()), status=200, dumps=for_dump)
    # if not found
    else:
        return web.json_response({"status": "Not found"}, status=404)