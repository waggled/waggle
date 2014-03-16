#-*- coding: utf-8 -*-
from electionapp.settings import *
import uuid

def get_new_election_key():
    return str(uuid.uuid4()).replace('-','')[:KEYA_LEN]

def get_new_guest_key():
    return str(uuid.uuid4()).replace('-','')[:KEYB_LEN]

def get_random_username():
    return 'anon_'+str(uuid.uuid4()).replace('-','')[:20]