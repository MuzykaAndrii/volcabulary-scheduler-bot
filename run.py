from app.main import web, app
import os

if __name__ == '__main__':
    # the PORT env variable is defined automatically then heroku app is started
    web.run_app(app, port=os.environ.get("PORT", 5000))