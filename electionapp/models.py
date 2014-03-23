from mongoengine import *
import os
import sys
sys.path.append(os.path.abspath('..'))
from waggle.settings import DBNAME
import datetime
import tools
from django.contrib.auth.decorators import login_required
from mongoengine.django.auth import User

connect(DBNAME)

# SYSTEMS

class SystemDescription(EmbeddedDocument):
    ballot = StringField(max_length=255, required=True)
    computation = StringField(max_length=255, required=True)

class System(Document):
    key = StringField(max_length=3,required=True)
    name = StringField(max_length = 100, required = True)
    description = EmbeddedDocumentField(SystemDescription, required=True)


# ELECTIONS

class ElectionSystem(EmbeddedDocument):
    system = ReferenceField(System, required=True)
    custom = DictField()

class Election(Document):
    def delete(self, *args, **kwargs):
        for key,guest in self.guests.items():
            if self in guest.invited_to:
                guest.invited_to.remove(self)
                if len(guest.invited_to)==0:
                    del guest.invited_to
                guest.save()
            if self in guest.voted_in:
                guest.voted_in.remove(self)
                if len(guest.voted_in)==0:
                    del guest.voted_in
                guest.save()
        if not self.admin_user is None:
            self.admin_user.admin_of.remove(self)
            if len(self.admin_user.admin_of)==0:
                del self.admin_user.admin_of
                self.admin_user.save()
        for result in self.results:
            del result
        super(Election, self).delete(*args, **kwargs)
    
    def add_guest(self, user):
        if self.guests is None:
            self.guests = dict()
        for key,guest in self.guests.items():
            if guest==user:
                print 'This user is already invited'
                #TODO : do sthg
        self.guests[tools.get_new_guest_key()]=user
        if not user.invited_to is None:
            user.invited_to.append(self)
        else:
            user.invited_to = [self]
        user.save()

    def add_guest_by_email(self, email):
        matching_emails = MyUser.objects(email=email)
        if matching_emails.count()==0:
            user = MyUser()
            user.type = 2
            user.email = email
            user.save()
        else:
            user = matching_emails[0]
        self.add_guest(user)

    key = StringField(max_length=16, required=True)
    type = IntField(required=True)
    admin_key = StringField(max_length=8, required=True)
    admin_user = ReferenceField('MyUser')
    open = BooleanField(required=True)
    name = StringField(max_length=120, required=True)
    candidates = DictField(required=True)
    message = StringField(max_length=1000)
    systems = ListField(EmbeddedDocumentField(ElectionSystem))
    guests = DictField()
    results = ListField(ReferenceField('Result'))
    creation_date = DateTimeField(required=True)
    closing_date = DateTimeField()

# RESULTS

class ResultRanking(EmbeddedDocument):
    candidate = StringField(required=True)
    rank = IntField(required=True)
    score = FloatField()

class Result(Document):
    system = ReferenceField(System)
    election = ReferenceField(Election, reverse_delete_rule=CASCADE)
    up_to_date = BooleanField(required = True)
    date = DateTimeField(required = True)
    ranking = ListField(EmbeddedDocumentField(ResultRanking))

# USERS

class MyUser(User):
    def __init__(self, *args, **kwargs):
        super(MyUser, self).__init__(*args, **kwargs)
        self.date=datetime.datetime.now()
    def save(self, *args, **kwargs):
        if not self.email is None:
            self.username=self.email
        else:
            self.username=tools.get_random_username()
        super(User, self).save(*args, **kwargs)
    type = IntField()
    email = EmailField()
    fb_id = StringField()
    password = StringField()
    invited_to = ListField(ReferenceField(Election))
    voted_in = ListField(ReferenceField(Election))
    admin_of = ListField(ReferenceField(Election))
    name = StringField(max_length=255)
    ip = StringField(max_length=20)
    date = DateTimeField(required=True)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=[]

# BALLOTS

class BallotContent(EmbeddedDocument):
    candidate = StringField(required = True)
    rank = IntField()
    score = FloatField()

class Ballot(Document):
    def delete(self, *args, **kwargs):
        self.user.voted_in.remove(self.election)
        super(Ballot, self).delete(*args, **kwargs)
    system = ReferenceField(System, required=True)
    election = ReferenceField(Election, required=True, reverse_delete_rule=CASCADE)
    user = ReferenceField(MyUser,required=True)
    content = ListField(EmbeddedDocumentField(BallotContent))
    date = DateTimeField(required=True)
