from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

__all__ = ['session', 'db', 'migrate', 'login']

session = Session()
db = SQLAlchemy()
migrate = Migrate(db=db)
login = LoginManager()
