#-*- coding: utf-8 -*-
from models import *
import datetime

def cast_ballot(form_data, user, system, election):
    ballot = Ballot()
    ballot.date = datetime.datetime.now()
    ballot.system = system
    ballot.election = election
    ballot.user = user
    method_name = 'get_ballot_content_'+system.key
    method = globals()[method_name]
    ballot.content = method(form_data)
    ballot.save()
    if not election in user.voted_in:
        user.voted_in.append(election)
    user.update(set__voted_in=user.voted_in)
    for result in election.results:
        if result.system == system:
            result.up_to_date = False
            result.save()
    return

def get_ballot_content_FPP(form_data):
    ballot_content = BallotContent()
    ballot_content.candidate = form_data['candidates']
    return [ballot_content]

def get_form_data_FPP(ballot_content):
    form_data = dict()
    form_data['candidates'] = ballot_content[0]['candidate']
    return form_data

def get_form_data_BDA(ballot_content):
    s = ''
    d_ranks = dict()
    for item in ballot_content:
        d_ranks[item.rank] = item.candidate
    for item in sorted(d_ranks.items()):
        s=s+item[1]+';'
    return {'ranking':s}

def get_form_data_RGV(ballot_content):
    form_data = dict()
    for item in ballot_content:
        form_data[item.candidate] = int(item.score)
    return form_data

def get_ballot_content_RGV(form_data):
    res = []
    for key,value in form_data.items():
        ballot_content = BallotContent()
        ballot_content.candidate = key
        ballot_content.score = value
        res.append(ballot_content)
    return res

def get_ballot_content_BDA(form_data):
    res=[]
    current_rank=1
    list_cands = form_data['ranking'][:-1].split(';')
    for cand in list_cands:
        ballot_content=BallotContent()
        ballot_content.candidate=cand
        ballot_content.rank = current_rank
        current_rank = current_rank+1
        res.append(ballot_content)
    return res

def check_and_compute(election):
    """
        Computes all (for each system) results of an election that are not up to date, and returns the election document.
        Parameters:
        election - a document of type Election
    """
    for election_system in election.systems:
        system = election_system.system
        results_already_computed = False
        for result in election.results:
            if result.system == system and result.up_to_date:
                results_already_computed = True
        if not results_already_computed:
            new_results = []
            for result in election.results:
                if result.system == system:
                    result.delete()
                else:
                    new_results.append(result)
            election.results = new_results
            method_name = 'compute' + system.key
            method = globals()[method_name]
            ranking = method(election.id, election.candidates, system)
            result = Result(date=datetime.datetime.now(), ranking=ranking, system=system, up_to_date=True, election=election)
            result.save()
            election.results.append(result)
    election.save()
    return election

def computeFPP(election_id, candidates, system):
    """
        Returns the FPP ranking of candidates for an election (as a list of ResultRanking documents)
        Parameters:
        election_id - ObjectId id of election
        candidates - election.candidates
        system - System object (should be FPP)
        """
    ballots = Ballot.objects(election=election_id, system=system)
    res = dict()
    for key in candidates:
        res[key] = 0.
    for ballot in ballots:
        cand = ballot.content[0].candidate
        res[cand] = res[cand] + 1.
    return get_ranking_from_scores(candidates,res)

def computeBDA(election_id, candidates, system):
    """
        Returns the FPP ranking of candidates for an election (as a list of ResultRanking documents)
        Parameters:
        election_id - ObjectId id of election
        candidates - election.candidates
        system - System object (should be Borda)
        """
    ballots = Ballot.objects(election=election_id, system=system)
    res = dict()
    for key in candidates:
        res[key] = 0.
    for ballot in ballots:
        k = len(candidates)
        for item in ballot.content:
            cand = item.candidate
            res[cand] = res[cand] + k
            k = k-1
    return get_ranking_from_scores(candidates,res)

def computeRGV(election_id, candidates, system):
    """
        Returns the RGV ranking of candidates for an election (as a list of ResultRanking documents)
        Parameters:
        election_id - ObjectId id of election
        candidates - election.candidates
        system - System object (should be Borda)
    """
    print 'Computing RGV results...'
    ballots = Ballot.objects(election=election_id, system=system)
    res = dict()
    for key in candidates:
        res[key] = 0.
    for ballot in ballots:
        for item in ballot.content:
            cand = item.candidate
            res[cand] = res[cand] + item.score
    print res
    return get_ranking_from_scores(candidates,res)

def get_ranking_from_scores(candidates_names,d):
    """
        From a two dictionaries describing respectively the candidates's names and their scores, returns a list of documents of type ResultRanking, describing the ranking of candidates from highest score to lowest.
        Parameters:
        candidates_names - a dictionary where keys are candidates ids and values are their names
        d - a dictionary where keys are candidates ids and values are their scores
    """
    ranking = []
    current_rank = 0
    nb_ex_aequo = 1
    prev_score = float("inf") # Proceeding like this may cause flaws
    for item in reversed(sorted(d.items(), key=lambda x: x[1])):
        score = item[1]
        if score<prev_score:
            current_rank = current_rank + nb_ex_aequo
        else:
            nb_ex_aequo = nb_ex_aequo + 1
        temp = ResultRanking()
        temp.candidate = candidates_names[item[0]]
        temp.score = score
        temp.rank = current_rank
        prev_score=score
        ranking.append(temp)
    return ranking