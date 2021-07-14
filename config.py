import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    TOKEN = os.getenv('BOT_TOKEN')
    WEBHOOK = os.getenv('WEBHOOK')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))