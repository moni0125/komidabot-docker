import json
from typing import Dict, List, Optional, TypedDict, Union

from flask_login import UserMixin
from sqlalchemy.sql import functions

from extensions import db, ModelBase
from komidabot.util import expected


class AdminSubscription(TypedDict):
    endpoint: str  # XXX: This is a globally unique identifier for the client
    keys: Dict[str, str]


class RegisteredUser(ModelBase, UserMixin):
    __tablename__ = 'registered_users'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    provider = db.Column(db.String(16), nullable=False)
    subject = db.Column(db.String(), nullable=False)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    profile_picture = db.Column(db.String(), nullable=False)

    registered_on = db.Column(db.DateTime(), nullable=False, server_default=functions.now())
    activated_on = db.Column(db.DateTime(), nullable=True)

    web_subscriptions = db.Column(db.String(), nullable=False, server_default='[]')

    roles: 'List[Role]' = db.relationship('Role', secondary='user_roles', backref='user')
    submissions = db.relationship('LearningDatapointSubmission', backref='registered_user', passive_deletes=True)

    __table_args__ = (
        db.UniqueConstraint('provider', 'subject'),
    )

    def __init__(self, provider: str, subject: str, name: str, email: str, profile_picture: str):
        if not isinstance(provider, str):
            raise expected('provider', provider, str)
        if not isinstance(subject, str):
            raise expected('subject', subject, str)
        if not isinstance(name, str):
            raise expected('name', name, str)
        if not isinstance(email, str):
            raise expected('email', email, str)
        if not isinstance(profile_picture, str):
            raise expected('profile_picture', profile_picture, str)

        self.provider = provider
        self.subject = subject
        self.name = name
        self.email = email
        self.profile_picture = profile_picture

    @staticmethod
    def create(provider: str, subject: str, name: str, email: str, profile_picture: str,
               add_to_db=True) -> 'RegisteredUser':
        user = RegisteredUser(provider, subject, name, email, profile_picture)

        if add_to_db:
            db.session.add(user)

        return user

    def delete(self):
        db.session.delete(self)

    # Overrides UserMixin.is_active
    @property
    def is_active(self):
        return self.activated_on is not None

    # Query methods
    @staticmethod
    def get_by_id(user_id: int) -> 'Optional[RegisteredUser]':
        return RegisteredUser.query.filter_by(id=user_id).first()

    @staticmethod
    def find_by_provider_id(provider: str, subject: str) -> 'Optional[RegisteredUser]':
        return RegisteredUser.query.filter_by(provider=provider, subject=subject).first()

    @staticmethod
    def find_by_email(email: str) -> 'Optional[RegisteredUser]':
        return RegisteredUser.query.filter_by(email=email).first()

    @staticmethod
    def get_all() -> 'List[RegisteredUser]':
        return RegisteredUser.query.all()

    @staticmethod
    def get_all_active() -> 'List[RegisteredUser]':
        return RegisteredUser.query.filter(RegisteredUser.activated_on != None).all()

    @staticmethod
    def get_all_by_role(role: 'Role') -> 'List[RegisteredUser]':
        return RegisteredUser.query.filter(
            UserRoles.user_id == RegisteredUser.id,
            UserRoles.role_id == role.id
        ).all()

    # Roles functions
    def get_roles(self) -> 'List[Role]':
        return self.roles

    def add_role(self, role: 'Role'):
        self.roles.append(role)

    def remove_role(self, role: 'Role'):
        self.roles.remove(role)

    def is_role(self, role: 'Union[str, Role]') -> bool:
        if isinstance(role, str):
            role = Role.find_by_name(role)
            return role is not None and role in self.roles
        elif isinstance(role, Role):
            return role in self.roles
        else:
            raise ValueError('role')

    # Subscriptions functions
    def get_subscriptions(self) -> 'List[AdminSubscription]':
        return json.loads(self.web_subscriptions)

    def set_subscriptions(self, subscriptions: 'List[AdminSubscription]'):
        self.web_subscriptions = json.dumps(subscriptions)

    def add_subscription(self, endpoint: str, keys: Dict[str, str]):
        subscriptions: 'List[AdminSubscription]' = []
        found = False

        for sub in self.get_subscriptions():
            subscriptions.append(sub)

            if sub['endpoint'] == endpoint:
                found = True

        if not found:
            subscriptions.append({'endpoint': endpoint, 'keys': keys})

        self.set_subscriptions(subscriptions)

    def remove_subscription(self, endpoint: str):
        self.set_subscriptions([sub for sub in self.get_subscriptions() if sub['endpoint'] != endpoint])

    @staticmethod
    def replace_subscription(old_endpoint: str, endpoint: str, keys: Dict[str, str]):
        for user in RegisteredUser.get_all():
            user.set_subscriptions([sub if sub['endpoint'] != old_endpoint else {'endpoint': endpoint, 'keys': keys}
                                    for sub in user.get_subscriptions()])

    def __hash__(self):
        return hash(self.id)


class Role(ModelBase):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    users = db.relationship('RegisteredUser', secondary='user_roles', backref='role')

    def __init__(self, name: str):
        if not isinstance(name, str):
            raise expected('name', name, str)

        self.name = name

    @staticmethod
    def create(name: str, add_to_db=True) -> 'Role':
        user = Role(name)

        if add_to_db:
            db.session.add(user)

        return user

    @staticmethod
    def find_by_name(name: str) -> 'Optional[Role]':
        return Role.query.filter_by(name=name).first()


class UserRoles(ModelBase):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer(), db.ForeignKey('registered_users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
