#-*- coding: utf-8 -*-
from models import *
import datetime

def check_and_compute(election):
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
            ranking = method(election, system)
            result = Result()
            result.date = datetime.datetime.now()
            result.ranking = ranking
            result.system = system
            result.up_to_date = True
            result.save()
            election.results.append(result)
    election.save()
    return election

def computeFPP(election, system):
    ballots = Ballot.objects(election=election, system=system)
    res = dict()
    for key in election.candidates:
        res[key] = 0.
    for ballot in ballots:
        cand = ballot.content[0].candidate
        res[cand] = res[cand] + 1.
    return get_ranking_from_scores(election.candidates,res)

def get_ranking_from_scores(candidates_names,d):
    # This method returns a list of ResultRanking EmbeddedDocuments with d being a dictionary with candidates as keys and scores as values, ordered from winner to loser
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