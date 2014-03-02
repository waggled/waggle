from mongoengine import *
import os
import sys
sys.path.append(os.path.abspath('..'))
from waggle.settings import DBNAME
import datetime
import tools

connect(DBNAME)

# SYSTEMS

class SystemDescription(EmbeddedDocument):
    ballot = StringField(max_length=255, required=True)
    computation = StringField(max_length=255, required=True)

class System(Document):
    key = StringField(max_length=3,required=True)
    name = StringField(max_length = 100, required = True)
    description = EmbeddedDocumentField(SystemDescription, required=True)

# RESULTS

class ResultRanking(EmbeddedDocument):
    candidate = StringField(required=True)
    rank = IntField(required=True)
    score = FloatField()

class Result(Document):
    system = ReferenceField(System)
    up_to_date = BooleanField(required = True)
    date = DateTimeField(required = True)
    ranking = ListField(EmbeddedDocumentField(ResultRanking))

# ELECTIONS

class ElectionSystem(EmbeddedDocument):
    system = ReferenceField(System, required=True)
    custom = DictField()

class Election(Document):
    def __init__(self, *args, **kwargs):
        super(Election, self).__init__(*args, **kwargs)
        self.creation_date=datetime.datetime.now()
        self.key = tools.get_new_election_key()
        self.open=True
    key = StringField(max_length=16, required=True)
    type = IntField(required=True)
    admin_key = StringField(max_length=8, required=True)
    open = BooleanField(required=True)
    name = StringField(max_length=120, required=True)
    candidates = DictField(required=True)
    message = StringField(max_length=1000)
    systems = ListField(EmbeddedDocumentField(ElectionSystem))
    guests = DictField()
    results = ListField(ReferenceField(Result))
    creation_date = DateTimeField(required=True)
    closing_date = DateTimeField()

# USERS

class User(Document):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.date=datetime.datetime.now()
    type = IntField(required=True)
    email = EmailField()
    fb_id = StringField()
    password = StringField()
    invited_to = ListField(ReferenceField(Election))
    voted_in = ListField(ReferenceField(Election))
    admin_of = ListField(ReferenceField(Election))
    name = StringField(max_length=255)
    ip = StringField(max_length=20, required=True)
    date = DateTimeField(required=True)

# BALLOTS

class BallotContent(EmbeddedDocument):
    candidate = StringField(required = True)
    rank = IntField()
    score = FloatField()

class Ballot(Document):
    system = ReferenceField(System, required=True)
    election = ReferenceField(Election, required=True)
    user = ReferenceField(User,required=True)
    content = ListField(EmbeddedDocumentField(BallotContent))
    date = DateTimeField(required=True)
