#-*- coding: utf-8 -*-
from django import forms

class BallotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        custom = kwargs.pop('custom', None)
        super(BallotForm, self).__init__(*args, **kwargs)
        self.choices = choices
        self.custom = custom

class FPPBallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(FPPBallotForm, self).__init__(*args, **kwargs)
        self.fields['candidates'].choices = self.choices
    candidates = forms.ChoiceField(choices=(), widget=forms.RadioSelect)

class BDABallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(BDABallotForm, self).__init__(*args, **kwargs)
        self.fields['candidates'].choices = choices
    candidates = forms.ChoiceField(choices=()) #TODO : CHANGE TO DRAGNDROP

class RGVBallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(RGVBallotForm, self).__init__(*args, **kwargs)
        for choice in self.choices:
            self.fields[choice[0]] = forms.IntegerField(max_value=self.custom['max'], min_value=self.custom['min'],label=choice[1], required=True)