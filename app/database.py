from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, ForeignKey, Text
from functools import wraps
from config import Config
import json

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
    bundles = relationship('Bundle', backref='creator', lazy='dynamic')

    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

class Bundle(DbMixin, Base):
    __tablename__ = 'bundles'
    id = Column('id', Integer, primary_key=True, unique=True)
    creator_id = Column('creator_id', Integer, ForeignKey('users.id'), nullable=False)
    words = Column('words' ,Text, nullable=False)

    def __init__(self, creator_id):
        self.creator_id = creator_id
    
    @staticmethod
    def serialize_to_pretty(dict_words):
        words_pretty = tuple()
        for word, translation in dict_words.items():
            words_pretty += ({'word': word, 'translation': translation},)
        
        return {'dictionary': words_pretty}
    
    def encode_words(self, dict_words):
        self.words = json.dumps(dict_words, ensure_ascii=False)
    
    def decode_words(self):
        return json.loads(self.words)
    
    def generate_words_string(self):
        words_string = str()
        count = 0
        dict_words = self.decode_words()
        for word, translation in dict_words.items():
            count += 1
            words_string += f'{count}. {word} - {translation}\n'
        
        return words_string


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
