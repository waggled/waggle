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
                            ballots = Ballot.objects(election=election, user=election['guests'][keyB])
                            if ballots.count()==0: #TODO : distinguish
                                return vote(request, election, election['guests'][keyB])
                            else:
                                return vote(request, election, election['guests'][keyB])
                        else:
                            raise Http404
                else:
                    if election['open']:
                        return view_results(request, election)
                        #TODO: GO TO TEMPLATE RESULTS (and show "sorry")
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
                        try:
                            ip = request.META['HTTP_X_FORWARDED_FOR']
                        except KeyError:
                            ip = request.META['REMOTE_ADDR']
                        user = User(ip=ip, date=datetime.datetime.now(), type=9)
                        user.save() #CAUTION : A USER IS CREATED EVEN IF THE VOTE IS NOT VALIDATED
                        return vote(request, election, user)
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
    return render_to_response('admin_election.html', {'election': election})

def view_results(request, election):
    election = results.check_and_compute(election)
    return render_to_response('view_results.html', {'election': election})

def vote(request, election, user):
    #TODO: adapt to multiple systems by creating a metaForm
    my_choices = []
    for key, value in election.candidates.items():
        my_choices.append((key,value))
    if request.method == 'POST':
        for election_system in election.systems:
            method_name = election_system.system.key + 'BallotForm'
            method = globals()[method_name]
            form = method(request.POST, choices=my_choices, custom=election_system.custom)
        if form.is_valid():
            # TODO: Here we can process the data from the form  #HERE FOR FPP
            ballot = Ballot()
            ballot.date = datetime.datetime.now()
            ballot.user = User.objects[0] #TODO: modify
            ballot_content = BallotContent()
            ballot_content.candidate = form.cleaned_data['candidates']
            ballot.content = [ballot_content]
            ballot.system = System.objects(key='FPP')[0] #TODO: modify
            ballot.election = election
            ballot.save()
            return render_to_response('voting_page.html', {'form':form, 'send':True, 'election':election}, context_instance=RequestContext(request))
        else:
            return render_to_response('voting_page.html', {'form':form, 'send':False, 'election':election}, context_instance=RequestContext(request))
    else: # GET
        ballotForms=[]
        for election_system in election.systems:
            method_name = election_system.system.key + 'BallotForm'
            method = globals()[method_name]
            ballotForms.append(method(choices=my_choices, custom=election_system.custom))
        return render_to_response('voting_page.html', {'form':ballotForms[0], 'send':False, 'election':election}, context_instance=RequestContext(request))

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