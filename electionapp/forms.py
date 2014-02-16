#-*- coding: utf-8 -*-
from django import forms

class FPPBallotForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        custom = kwargs.pop('custom', None)
        super(FPPBallotForm, self).__init__(*args, **kwargs)
        if choices is not None:
            self.fields['candidates'].choices = choices
    candidates = forms.ChoiceField(choices=(), widget=forms.RadioSelect)
    # white vote allowed