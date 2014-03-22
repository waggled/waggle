#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.forms.formsets import formset_factory
from models import *
from results import *
import datetime
from electionapp.settings import *
from electionapp.forms import *
import time
import tools
from django.shortcuts import render
from django.core.urlresolvers import reverse
from mongoengine.django.auth import *
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout

def polls_overview(request):
	elections = Election.objects.order_by('-creation_date')
	return render_to_response('polls.html', {'Elections': elections},context_instance=RequestContext(request))

def users_overview(request):
    users = MyUser.objects.order_by('-date')
    return render_to_response('users.html', {'Users': users},context_instance=RequestContext(request))

def ballots_overview(request):
    ballots = Ballot.objects.order_by('-date')
    return render_to_response('ballots.html', {'Ballots': ballots},context_instance=RequestContext(request))

def results_overview(request):
    results = Result.objects.order_by('-date')
    return render_to_response('results.html', {'Results': results},context_instance=RequestContext(request))

def index(request):
	return render_to_response('index.html',context_instance=RequestContext(request))

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
    election = check_and_compute(election)
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
    #TODO: adapt to multiple systems
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
                user = MyUser(ip=ip, type=9)
                user.save()
            if already_voted:
                prev_ballots = Ballot.objects(user=user,election=election)
                for ballot in prev_ballots:
                    ballot.delete()
            cast_ballot(form.cleaned_data, user, election.systems[0].system, election)
            return render_to_response('voting_page.html', {'form':form, 'send':True, 'election':election, 'user_key':user_key, 'show_already_voted':False, 'show_form':False, 'show_edit':edit_vote, 'show_vote_cast':True}, context_instance=RequestContext(request))
        else:
            return render_to_response('voting_page.html', {'form':form, 'send':False, 'election':election, 'user_key':user_key, 'show_already_voted':False, 'show_form':True, 'show_edit':edit_vote, 'show_vote_cast':False}, context_instance=RequestContext(request))

    else: # GET
        ballotForms=[]
        if edit_vote:
            for election_system in election.systems:
                ballot = Ballot.objects(system=election_system.system, election=election, user=user)[0]
                method_name = 'get_form_data_'+election_system.system.key
                method = globals()[method_name]
                form_data = method(ballot.content)
                ballot_method_name = election_system.system.key + 'BallotForm'
                ballot_method = globals()[ballot_method_name]
                ballotForms.append(ballot_method(choices=my_choices, custom=election_system.custom, initial=form_data))
        else:
            for election_system in election.systems:
                method_name = election_system.system.key + 'BallotForm'
                method = globals()[method_name]
                ballotForms.append(method(choices=my_choices, custom=election_system.custom))
        return render_to_response('voting_page.html', {'form':ballotForms[0], 'send':False, 'election':election, 'user_key':user_key, 'show_already_voted':already_voted and not edit_vote, 'show_form':(not already_voted) or edit_vote, 'show_edit':edit_vote, 'show_vote_cast':False}, context_instance=RequestContext(request))

def create(request):
    CandidateFormSet = formset_factory(CandidateForm, max_num=10, formset=RequiredFormSet) #TODO: make max_num a settings.py parameter (caution, 10 is used in js too)
    EmailGuestFormSet = formset_factory(EmailGuestForm, max_num=10, formset=RequiredFormSet) #TODO: idem
    if request.method == 'POST':
        election_form = ElectionForm(request.POST, request.FILES, prefix='election')
        creator_form = CreatorForm(request.POST, request.FILES, prefix='creator')
        candidate_formset = CandidateFormSet(request.POST, request.FILES, prefix='candidate')
        emailguest_formset = EmailGuestFormSet(request.POST, request.FILES, prefix='emailguest')
        customsystem_forms = dict()
        customs_are_valid = True
        for system in System.objects:
            method_name = system.key+'CustomForm'
            method = globals()[method_name]
            customsystem_form = method(request.POST, request.FILES, prefix=system.key+'_custom')
            if not customsystem_form.is_valid():
                customs_are_valid = False
            customsystem_form = customsystem_form.cleaned_data
            customsystem_forms[system.key] = customsystem_form
        if election_form.is_valid() and candidate_formset.is_valid() and emailguest_formset.is_valid() and creator_form.is_valid() and customs_are_valid:
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
            key = election_form['system']
            election_system.system = System.objects(key=key)[0]
            if key=='RGV':
                custom = {'min':customsystem_forms['RGV']['min'],'max':customsystem_forms['RGV']['max']}
                election_system.custom=custom
            election_systems = []
            election_systems.append(election_system)
            new_election.systems = election_systems
            #CANDIDATES
            d_candidates = dict()
            k = 1
            for candidate_form in candidate_formset:
                candidate_form = candidate_form.cleaned_data
                d_candidates[str(k)] = candidate_form['name']
                k = k+1
            new_election.candidates = d_candidates
            new_election.save()
            #GUESTS
            if new_election.type=='1': # if there are guests
                d_guests = dict()
                for emailguest_form in emailguest_formset:
                    emailguest_form = emailguest_form.cleaned_data
                    matching_emails = MyUser.objects(email=emailguest_form['email'])
                    if matching_emails.count()==0:
                        user = MyUser()
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
                result.election = new_election
                result.system = System.objects(key=election_system.system.key)[0]
                result.up_to_date = False
                result.date = datetime.datetime.now()
                result.save()
                new_election.results.append(result)
            new_election.save()
            #Create admin user
            matching_admin = MyUser.objects(email = creator_form['email'])
            if matching_admin.count()==0:
                admin = MyUser()
                admin.type = 2
                if creator_form['email']<>'':
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
            new_election.admin_user = admin
            new_election.save()
            return render_to_response('create.html', {'success':True})
        else:
            return render_to_response('create.html', {'election_form':election_form, 'candidate_formset':candidate_formset, 'emailguest_formset': emailguest_formset,'creator_form':creator_form, 'customsystem_forms':customsystem_forms}, context_instance=RequestContext(request))
    else: # GET
        election_form = ElectionForm(prefix='election')
        creator_form = CreatorForm(prefix='creator')
        candidate_formset = CandidateFormSet(prefix='candidate')
        emailguest_formset = EmailGuestFormSet(prefix='emailguest')
        customsystem_forms = dict()
        for system in System.objects:
            key = system.key
            method_name = system.key + 'CustomForm'
            method = globals()[method_name]
            customsystem_forms[key] = method(prefix=key+'_custom')
        return render_to_response('create.html', {'election_form':election_form, 'candidate_formset':candidate_formset, 'emailguest_formset': emailguest_formset, 'creator_form':creator_form, 'customsystem_forms':customsystem_forms}, context_instance=RequestContext(request))

def systems(request):
    systems = System.objects
    return render_to_response('systems.html', {'systems':systems},context_instance=RequestContext(request))

@login_required
def dashboard(request):
	return render_to_response('dashboard.html',context_instance=RequestContext(request))

def about(request):
	return render_to_response('about.html',context_instance=RequestContext(request))

def custom_404(request):
    return render_to_response('404.html',context_instance=RequestContext(request))

def account(request):
    success = False
    if request.method == 'POST':
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            password_check = form.cleaned_data['password_check']
        #First check if email is taken
        matching_accounts = MyUser.objects(email=email, type=1)
        if matching_accounts.count()>0:
            message = 'Account already exists.'
        else:
            if password <> password_check:
                message='Password verification failed.'
            else:
                    message = 'Account created. Please confirm your email by clicking on the link we sent you.'
                    matching_users = MyUser.objects(email=email)
                    if matching_users.count()>0:
                        existing_user = matching_users[0]
                        existing_user.set_password(password)
                        existing_user.type = 1
                        existing_user.name = name
                        existing_user.save()
                    else:
                        #TODO : create a new user
                        user = MyUser.create_user(email, password, email)
                        user.type = 1
                        user.name = name
                        try:
                            ip = request.META['HTTP_X_FORWARDED_FOR']
                        except KeyError:
                            ip = request.META['REMOTE_ADDR']
                        user.ip = ip
                        user.save()
                    success=True
                    return render_to_response('account.html', locals(), context_instance=RequestContext(request))
        return render_to_response('account.html', locals(), context_instance=RequestContext(request))
    else:
        form = AccountCreationForm()
        return render_to_response('account.html', locals(), context_instance=RequestContext(request))

def login(request):
    error = False
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            backend = MongoEngineBackend()
            username = form.cleaned_data['username']  # Nous récupérons le nom d'utilisateur
            password = form.cleaned_data['password']  # … et le mot de passe
            user = backend.authenticate(username=username, password=password)  #Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                django_login(request, user)  # nous connectons l'utilisateur
            else: #sinon une erreur sera affichée
                error = True
    else:
        form = LoginForm()
    return render_to_response('login.html',locals(), context_instance=RequestContext(request))

@login_required
def logout(request):
    django_logout(request)
    return redirect(reverse(login))

def delete_election(request, key):
    #TODO: remove this election form voted_in, admin_of, etc
    el = Election.objects(key=key)[0]
    el.delete()
    return redirect(polls_overview)