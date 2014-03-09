#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.forms.formsets import formset_factory
from models import *
import results
import datetime
from electionapp.settings import *
from electionapp.forms import *
import time
import tools

def polls_overview(request):
	elections = Election.objects
	return render_to_response('polls.html', {'Elections': elections})

def index(request):
	return render_to_response('index.html')

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
            return render_to_response('voting_page.html', {'form':form, 'send':True, 'election':election, 'user_key':user_key, 'show_already_voted':False, 'show_form':False, 'show_edit':edit_vote, 'show_vote_cast':True}, context_instance=RequestContext(request))
        else:
            return render_to_response('voting_page.html', {'form':form, 'send':False, 'election':election, 'user_key':user_key, 'show_already_voted':False, 'show_form':True, 'show_edit':edit_vote, 'show_vote_cast':False}, context_instance=RequestContext(request))

    else: # GET
        ballotForms=[]
        #TODO : load previous ballots and put it in form variable
        for election_system in election.systems:
            method_name = election_system.system.key + 'BallotForm'
            method = globals()[method_name]
            ballotForms.append(method(choices=my_choices, custom=election_system.custom))
        return render_to_response('voting_page.html', {'form':ballotForms[0], 'send':False, 'election':election, 'user_key':user_key, 'show_already_voted':already_voted and not edit_vote, 'show_form':not already_voted, 'show_edit':edit_vote, 'show_vote_cast':False}, context_instance=RequestContext(request))

def create(request):
    CandidateFormSet = formset_factory(CandidateForm, max_num=10, formset=RequiredFormSet) #TODO: make max_num a settings.py parameter (caution, 10 is used in js too)
    EmailGuestFormSet = formset_factory(EmailGuestForm, max_num=10, formset=RequiredFormSet) #TODO: idem
    if request.method == 'POST':
        election_form = ElectionForm(request.POST, request.FILES, prefix='election')
        creator_form = CreatorForm(request.POST, request.FILES, prefix='creator')
        candidate_formset = CandidateFormSet(request.POST, request.FILES, prefix='candidate')
        emailguest_formset = EmailGuestFormSet(request.POST, request.FILES, prefix='emailguest')
        if election_form.is_valid() and candidate_formset.is_valid() and emailguest_formset.is_valid() and creator_form.is_valid():
            print 'Forms are valid.'
            election_form = election_form.cleaned_data
            creator_form = creator_form.cleaned_data
            # Create election
            new_election = Election()
            new_election.admin_key = tools.get_new_guest_key()
            new_election.key = tools.get_new_election_key()
            new_election.creation_date = datetime.datetime.now()
            new_election.open = True
            new_election.name = election_form['name']
            new_election.message = election_form['message']
            new_election.type = election_form['type']
            election_system = ElectionSystem()
            election_system.system = System.objects(key=election_form['system'])[0]
            election_systems = []
            election_systems.append(election_system) #TODO : change because this will only work for FPP
            new_election.systems = election_systems
            #CANDIDATES
            d_candidates = dict()
            k = 1
            for candidate_form in candidate_formset:
                candidate_form = candidate_form.cleaned_data
                d_candidates[str(k)] = candidate_form['name']
                k = k+1
            new_election.candidates = d_candidates
            print new_election
            new_election.save()
            #GUESTS
            d_guests = dict()
            for emailguest_form in emailguest_formset:
                emailguest_form = emailguest_form.cleaned_data
                matching_emails = User.objects(email=emailguest_form['email'])
                if matching_emails.count()==0:
                    user = User()
                    user.type = 2
                    user.email = emailguest_form['email']
                    user.invited_to = [new_election]
                
                else:
                    user = matching_emails[0]
                    if not user.invited_to is None:
                        user.invited_to.append(new_election)
                    else:
                        user.invited_to = [new_election]
                user.save()
                d_guests[tools.get_new_guest_key()] = user
            new_election.guests = d_guests
            #RESULTS
            new_election.results = []
            for election_system in new_election.systems:
                result = Result()
                result.system = System.objects(key=election_system.system.key)[0]
                result.up_to_date = False
                result.date = datetime.datetime.now()
                result.save()
                new_election.results.append(result)
            new_election.save()
            #Create admin user
            if 'email' in creator_form.keys():
                matching_admin = User.objects(email = creator_form['email'])
                if matching_admin.count()==0:
                    admin = User()
                    admin.type = 2
                    if not creator_form['email'] is None:
                        admin.email = creator_form['email']
                    try:
                        ip = request.META['HTTP_X_FORWARDED_FOR']
                    except KeyError:
                        ip = request.META['REMOTE_ADDR']
                    admin.ip = ip
                    admin.admin_of = [new_election]
                else:
                    admin = matching_admin[0]
                    if not admin.admin_of is None:
                        admin.admin_of.append(new_election)
                    else:
                        admin.admin_of = [new_election]
                admin.save()
            return render_to_response('create.html', {'success':True})
        else:
            return render_to_response('create.html', {'election_form':election_form, 'candidate_formset':candidate_formset, 'emailguest_formset': emailguest_formset}, context_instance=RequestContext(request))
    else: # GET
        election_form = ElectionForm(prefix='election')
        creator_form = CreatorForm(prefix='creator')
        candidate_formset = CandidateFormSet(prefix='candidate')
        emailguest_formset = EmailGuestFormSet(prefix='emailguest')
        return render_to_response('create.html', {'election_form':election_form, 'candidate_formset':candidate_formset, 'emailguest_formset': emailguest_formset, 'creator_form':creator_form}, context_instance=RequestContext(request))

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

