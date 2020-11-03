import datetime
import enum
import json
from typing import Any, List, NamedTuple, Optional, TypedDict, Union

from sqlalchemy.sql import expression

from extensions import db, ModelBase
from komidabot.models_users import RegisteredUser
from komidabot.util import expected

# ChoiceSchemaType = NamedTuple('ChoiceType', (('display', str), ('value', Any),))
#
#
# class SchemaElementType(enum.Enum):
#     STATIC_TEXT = 1  # Value type: str; always readonly
#     STATIC_IMAGE = 2  # Value type: str (base64 encoded data); always readonly
#     DIVIDER = 3  # Value type: nothing; always readonly
#     BOOLEAN = 4  # Value type: nothing
#     CHOICE = 5  # Value type: List[ChoiceType]
#     MULTIPLE_CHOICE = 6  # Value type: List[ChoiceType]
#     TEXT = 7  # Value type: nothing
#     NUMBER = 8  # Value type: nothing
#
#
# class SchemaElement(TypedDict):
#     type: int  # SchemaElementType
#     description: Optional[str]
#     readonly: Optional[bool]
#
#
# DataElement = Union[str, List[ChoiceSchemaType], None]
#
#
# class TrainingSchema(ModelBase):
#     __tablename__ = 'training_schema'
#
#     id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
#     name = db.Column(db.String(), nullable=False)
#     schema = db.Column(db.String(), nullable=False)
#
#     def __init__(self, name: str, schema: str):
#         if not isinstance(name, str):
#             raise expected('name', name, str)
#         if not isinstance(schema, str):
#             raise expected('schema', schema, str)
#
#         self.name = name
#         self.schema = schema
#
#     @staticmethod
#     def create(name: str, schema: 'List[SchemaElement]', add_to_db=True) -> 'TrainingSchema':
#         if not isinstance(schema, list):
#             raise expected('schema', schema, list)
#         for element in schema:
#             if not isinstance(element, dict):
#                 raise expected('schema[]', element, dict)
#             if 'type' not in element:
#                 raise ValueError('Missing type in SchemaElement')
#
#         # FIXME: Verify schema
#         result = TrainingSchema(name, json.dumps(schema))
#
#         if add_to_db:
#             db.session.add(result)
#
#         return result
#
#     @staticmethod
#     def find_by_id(schema_id: int) -> 'Optional[TrainingSchema]':
#         return TrainingSchema.query.filter_by(id=schema_id).first()
#
#     def get_schema(self) -> 'List[SchemaElement]':
#         return json.loads(self.schema)
#
#     def add_input(self, data: 'List[DataElement]',
#                   add_to_db=True) -> 'Optional[TrainingInput]':
#         # FIXME: Verify data
#         result = TrainingInput(self.id, json.dumps(data))
#
#         if add_to_db:
#             db.session.add(result)
#
#         return result
#
#
# class TrainingInput(ModelBase):
#     __tablename__ = 'training_input'
#
#     id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
#     schema_id = db.Column(db.Integer(), db.ForeignKey('training_schema.id'), nullable=False)
#     data = db.Column(db.String(), nullable=False)
#
#     def __init__(self, schema_id: int, data: str):
#         if not isinstance(schema_id, int):
#             raise expected('schema_id', schema_id, int)
#         if not isinstance(data, str):
#             raise expected('data', data, str)
#
#         self.schema_id = schema_id
#         self.data = data
#
#     @staticmethod
#     def find_by_id(input_id: int) -> 'Optional[TrainingInput]':
#         return TrainingInput.query.filter_by(id=input_id).first()
#
#     @staticmethod
#     def get_random(user: 'RegisteredUser') -> 'Optional[TrainingInput]':
#         return TrainingInput.query.order_by(expression.func.random()).filter(
#             expression.not_(
#                 TrainingResponse.query.filter(
#                     TrainingInput.id == TrainingResponse.input_id,
#                     TrainingResponse.user_id == user.id
#                 ).exists()
#             )
#         ).first()
#
#     def add_response(self, user: 'RegisteredUser', data: Any, add_to_db=True):
#         # FIXME: Verify data
#         result = TrainingResponse(self.id, user.id, json.dumps(data))
#
#         if add_to_db:
#             db.session.add(result)
#
#         return result
#
#
# class TrainingResponse(ModelBase):
#     __tablename__ = 'training_response'
#
#     id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
#     input_id = db.Column(db.Integer(), db.ForeignKey('training_input.id'), nullable=False)
#     user_id = db.Column(db.Integer(), db.ForeignKey('registered_users.id', onupdate='CASCADE', ondelete='CASCADE'),
#                         nullable=False)
#     data = db.Column(db.String(), nullable=False)
#
#     def __init__(self, input_id: int, user_id: int, data: str):
#         if not isinstance(input_id, int):
#             raise expected('input_id', input_id, int)
#         if not isinstance(user_id, int):
#             raise expected('user_id', user_id, int)
#         if not isinstance(data, str):
#             raise expected('data', data, str)
#
#         self.input_id = input_id
#         self.user_id = user_id
#         self.data = data


class LearningDatapoint(ModelBase):
    __tablename__ = 'learning_datapoint'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer(), db.ForeignKey('campus.id'), nullable=False)
    menu_day = db.Column(db.Date(), nullable=False)
    screenshot = db.Column(db.Text(), nullable=False)
    processed_data = db.Column(db.Text(), nullable=False)

    submissions = db.relationship('LearningDatapointSubmission', backref='datapoint', passive_deletes=True)

    def __init__(self, campus_id: int, menu_day: datetime.date, screenshot: str, processed_data: Any):
        if not isinstance(campus_id, int):
            raise expected('campus_id', campus_id, int)
        if not isinstance(menu_day, datetime.date):
            raise expected('menu_day', menu_day, datetime.date)
        if screenshot is None:
            raise ValueError('screenshot expected not None')
        if processed_data is None:
            raise ValueError('processed_data expected not None')

        self.campus_id = campus_id
        self.menu_day = menu_day
        self.screenshot = screenshot
        self.processed_data = json.dumps(processed_data)

    @staticmethod
    def create(campus: 'Campus', menu_day: datetime.date, screenshot: str,
               processed_data: Any) -> 'Optional[LearningDatapoint]':
        datapoint = LearningDatapoint(campus.id, menu_day, screenshot, processed_data)

        db.session.add(datapoint)

        return datapoint

    @staticmethod
    def find_by_id(datapoint_id: int) -> 'Optional[LearningDatapoint]':
        return LearningDatapoint.query.filter_by(id=datapoint_id).first()

    @staticmethod
    def get_all() -> 'List[LearningDatapoint]':
        return LearningDatapoint.query.all()

    @staticmethod
    def get_random(user: 'RegisteredUser') -> 'Optional[LearningDatapoint]':
        return LearningDatapoint.query.order_by(expression.func.random()).filter(
            expression.not_(
                LearningDatapointSubmission.query.filter(
                    LearningDatapoint.id == LearningDatapointSubmission.datapoint_id,
                    LearningDatapointSubmission.user_id == user.id
                ).exists()
            )
        ).first()

    def user_submit(self, user: 'RegisteredUser', submission_data: Any):
        LearningDatapointSubmission.create(self, user, submission_data)

    def __hash__(self):
        return hash(self.id)


class LearningDatapointSubmission(ModelBase):
    __tablename__ = 'learning_datapoint_submission'

    user_id = db.Column(db.Integer(),
                        db.ForeignKey('registered_users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)
    datapoint_id = db.Column(db.Integer(),
                             db.ForeignKey('learning_datapoint.id', onupdate='CASCADE', ondelete='CASCADE'),
                             primary_key=True)
    submission_data = db.Column(db.Text(), nullable=False)

    def __init__(self, user_id: int, datapoint_id: int, submission_data: Any):
        if not isinstance(user_id, int):
            raise expected('user_id', user_id, int)
        if not isinstance(datapoint_id, int):
            raise expected('datapoint_id', datapoint_id, int)
        if submission_data is None:
            raise ValueError('submission_data expected not None')

        self.user_id = user_id
        self.datapoint_id = datapoint_id
        self.submission_data = json.dumps(submission_data)

    @staticmethod
    def create(datapoint: LearningDatapoint, user: 'RegisteredUser',
               submission_data: Any) -> 'Optional[LearningDatapointSubmission]':
        submission = LearningDatapointSubmission(user.id, datapoint.id, submission_data)

        db.session.add(submission)

        return submission

    def __hash__(self):
        return hash((self.user_id, self.datapoint_id))
