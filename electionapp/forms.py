#-*- coding: utf-8 -*-
from django import forms

class ElectionForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=140, required=True, label='Name of the poll')
    message = forms.CharField(min_length=0, max_length=1000, label='Message to the voters')
    type = forms.ChoiceField(choices=[(1,'Only guests are allowed to vote'),(2,'Anyone can vote any number of times')], widget=forms.RadioSelect, required=True, label='Voting mode')
    #open
    #candidates
    #systems
    #guests

class BallotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        custom = kwargs.pop('custom', None)
        super(BallotForm, self).__init__(*args, **kwargs)
        self.choices = choices
        self.custom = custom
        self.requires_ranking = False

class FPPBallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(FPPBallotForm, self).__init__(*args, **kwargs)
        self.fields['candidates'].choices = self.choices
    candidates = forms.ChoiceField(choices=(), widget=forms.RadioSelect, required=True)

class BDABallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(BDABallotForm, self).__init__(*args, **kwargs)
        self.requires_ranking = True
    ranking = forms.CharField(max_length=1000, required=True)# TODO: rajouter l'argument widget=forms.HiddenInput()

class RGVBallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(RGVBallotForm, self).__init__(*args, **kwargs)
        for choice in self.choices:
            self.fields[choice[0]] = forms.IntegerField(max_value=self.custom['max'], min_value=self.custom['min'],label=choice[1], required=True)