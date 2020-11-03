from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import BaseQuery, Model, SQLAlchemy

__all__ = ['session', 'db', 'migrate', 'login', 'ModelBase']

session = Session()
db = SQLAlchemy()
migrate = Migrate(db=db)
login = LoginManager()


class _ModelBase(Model):
    query: BaseQuery


ModelBase: _ModelBase = db.Model
