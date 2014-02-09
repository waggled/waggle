#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from models import *
import datetime
from electionapp.settings import *

def index(request):
	#election = Election(name='Hello', creation_date=datetime.datetime.now())
	#election.save()
	#Election.drop_collection()
	elections = Election.objects
	return render_to_response('index.html', {'Elections': elections})

def analyze_key(request, key):
    if len(key) >= KEYA_LEN: #if key is long enough to identify a keyA
        keyA = key[:KEYA_LEN]
        election = Election.objects(key=keyA) #retrieve election data for keyA
        if len(election)==1: #if an election with id keyA was found
            election = election[0]
            keyB = key[KEYA_LEN:]
            if election['type']==1: #if election is private
                if len(keyB) == KEYB_LEN:
                    if keyB==election['admin_key']:
                        return admin_election(request, election['id'])
                    else:
                        if keyB in election['guests']: #if keyB is a guest key
                            ballots = Ballot.objects(election=election, user=election['guests'][keyB])
                            if ballots.count()==0: #TODO : distinguish
                                return voting_page(request, election['id'], election['guests'][keyB]['id'])
                            else:
                                return voting_page(request, election['id'], election['guests'][keyB]['id'])
                        else:
                            raise Http404
                else:
                    if election['open']:
                        redirect('http://www.google.fr')
                        #TODO: GO TO TEMPLATE RESULTS (and show "sorry")
                    else:
                        return view_results(election['id'])
            elif election['type']==2: #else if election is public #TO BE TESTED
                if len(keyB) == KEYB_LEN:
                    if keyB == election['admin_key']: #if keyB is the admin key
                        return admin_election(election['id'])
                    else:
                        raise Http404
                elif keyB == '':
                    if election['open']:
                        user = User(ip = request.META['HTTP_X_FORWARDED_FOR'], date=datetime.datetime.now())
                        user.save() #CAUTION : A USER IS CREATED EVEN IF THE VOTE IS NOT VALIDATED
                        return voting_page(request, election['id'], user['id'])
                    else:
                        return view_results(election['id'])
                else:
                    raise Http404
            else:
                raise Http404
        elif len(election)>1:
            raise Http404
            #TODO : raise error, because getting here means that more than 1 election with key keyA has been found
        else:
            raise Http404
    else:
        raise Http404

def admin_election(request, election_id):
    return render_to_response('admin_election.html')

def view_results(request, election_id):
    return render_to_response('view_results.html')

def voting_page(request, election_id, user_id):
    return render_to_response('voting_page.html')

def create(request):
	return render_to_response('index.html')

def systems(request):
	return render_to_response('index.html')

def dashboard(request):
	return render_to_response('index.html')

def account(request):
	return render_to_response('index.html')

def about(request):
	return render_to_response('about.html')