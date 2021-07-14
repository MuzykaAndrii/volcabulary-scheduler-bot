from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, ForeignKey
from functools import wraps
from config import Config

engine = create_engine(Config.DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class DbMixin(object):
    def save(self):
        session.add(self)
        session.commit()
        session.close()
    
    def delete(self):
        session.delete(self)
        session.commit()
        session.close()

class User(DbMixin, Base):
    __tablename__ = 'users'

    id = Column('id', Integer, primary_key=True, unique=True)
    telegram_id = Column('telegram_id', Integer, unique=True)

    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

def manage_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = args[0]
        current_user_telegram_id = response.chat.id
        current_user = session.query(User).filter_by(telegram_id=current_user_telegram_id).first()

        if not current_user:
            new_user = User(current_user_telegram_id)
            try:
                new_user.save()
            except BaseException:
                print(f'Failed to save user to database, telegram_id: {current_user_telegram_id}')

        return f(*args, **kwargs)
    return decorated_function

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)