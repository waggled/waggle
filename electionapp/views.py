#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from models import *
import results
import datetime
from electionapp.settings import *
from electionapp.forms import *
import time

def index(request):
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
                        return admin_election(request, election)
                    else:
                        if keyB in election['guests']: #if keyB is a guest key
                            if election['open']:
                                ballots = Ballot.objects(election=election, user=election['guests'][keyB])
                                if ballots.count()==0: #TODO : distinguish
                                    return vote(request, election, user=election['guests'][keyB], user_key=keyB)
                                else:
                                    return vote(request, election, user=election['guests'][keyB], user_key=keyB, already_voted=True)
                            else:
                                return view_results(request, election)
                        else:
                            raise Http404
                else:
                    if election['open']:
                        return view_results(request, election)
                    else:
                        return view_results(request, election)
            elif election['type']==2: #else if election is public #TO BE TESTED
                if len(keyB) == KEYB_LEN:
                    if keyB == election['admin_key']: #if keyB is the admin key
                        return admin_election(request, election)
                    else:
                        raise Http404
                elif keyB == '':
                    if election['open']:
                        return vote(request, election)
                    else:
                        return view_results(request, election)
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

def admin_election(request, election):
    return render_to_response('admin_election.html', {'election': election}, context_instance=RequestContext(request))

def view_results(request, election):
    election = results.check_and_compute(election)
    return render_to_response('view_results.html', {'election': election}, context_instance=RequestContext(request))

def close_election(request, key, open=False):
    #TODO : check if keys are ok here (important)
    election_key = key[:KEYA_LEN]
    admin_key = key[KEYA_LEN:]
    election = Election.objects(key=election_key)
    if len(election)==1: # if the election was found
        election=election[0]
        if election.admin_key==admin_key:
            if open: #for dev only
                election.open=True
                del election.closing_date
                election.save()
                return admin_election(request,election)
            else:
                election.open=False
                election.closing_date=datetime.datetime.now()
                election.save()
                return view_results(request,election)
        else:
            raise Http404
    else:
        raise Http404

def edit_vote(request,key):
    election_key = key[:KEYA_LEN]
    user_key = key[KEYA_LEN:]
    election = Election.objects(key=election_key)
    if len(election)==1: # if the election was found
        election=election[0]
        if user_key in election['guests']:
            if election['open']:
                ballots = Ballot.objects(election=election, user=election['guests'][user_key])
                if ballots.count()==0: #TODO : distinguish
                    raise Http404
                else:
                    return vote(request, election, user=election['guests'][user_key], user_key=user_key, already_voted=True, edit_vote=True)
            else:
                return view_results(request, election)
        else:
            raise Http404
    else:
        raise Http404

def vote(request, election, user=None, user_key='', already_voted=False, edit_vote=False):
    #TODO: adapt to multiple systems by creating a metaForm
    my_choices = []
    for key, value in election.candidates.items():
        my_choices.append((key,value))
    if request.method == 'POST':
        if already_voted:
            #TODO : load previous ballots and put it in form variable
            return render_to_response('voting_page.html', {'form':None, 'send':False, 'election':election, 'user_key':user_key, 'already_voted':already_voted, 'edit_vote':edit_vote}, context_instance=RequestContext(request))
        else:
            for election_system in election.systems:
                method_name = election_system.system.key + 'BallotForm'
                method = globals()[method_name]
                form = method(request.POST, choices=my_choices, custom=election_system.custom)
            if form.is_valid():
                if user==None:
                    try:
                        ip = request.META['HTTP_X_FORWARDED_FOR']
                    except KeyError:
                        ip = request.META['REMOTE_ADDR']
                    user = User(ip=ip, type=9)
                    user.save()
                results.cast_ballot(form.cleaned_data, user, election.systems[0].system, election)
                return render_to_response('voting_page.html', {'form':form, 'send':True, 'election':election, 'user_key':user_key, 'already_voted':already_voted, 'edit_vote':edit_vote}, context_instance=RequestContext(request))
            else:
                return render_to_response('voting_page.html', {'form':form, 'send':False, 'election':election, 'user_key':user_key, 'already_voted':already_voted, 'edit_vote':edit_vote}, context_instance=RequestContext(request))

    else: # GET
        ballotForms=[]
        for election_system in election.systems:
            method_name = election_system.system.key + 'BallotForm'
            method = globals()[method_name]
            ballotForms.append(method(choices=my_choices, custom=election_system.custom))
        return render_to_response('voting_page.html', {'form':ballotForms[0], 'send':False, 'election':election, 'user_key':user_key, 'already_voted':already_voted, 'edit_vote':edit_vote}, context_instance=RequestContext(request))

def create(request):
	return render_to_response('create.html')

def systems(request):
    systems = System.objects
    return render_to_response('systems.html', {'systems':systems})

def dashboard(request):
	return render_to_response('index.html')

def account(request):
	return render_to_response('index.html')

def about(request):
	return render_to_response('about.html')

def custom_404(request):
    return render_to_response('404.html')

