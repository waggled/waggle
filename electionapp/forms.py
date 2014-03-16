#-*- coding: utf-8 -*-
from django import forms
from models import *
from django.forms.formsets import BaseFormSet


class LoginForm(forms.Form):
    username = forms.CharField(label='Email', max_length=30)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class AccountCreationForm(forms.Form):
    name = forms.CharField(label='Name', required=True)
    email = forms.EmailField(label='Email', required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password_check = forms.CharField(label='Password verification', widget=forms.PasswordInput, required=True)

class RequiredFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

class RGVCustomForm(forms.Form):
    min = forms.IntegerField(required=False, initial=0, widget=forms.HiddenInput()) #TODO : handle dynamically 'required' argument
    max = forms.IntegerField(required=False, initial=20, widget=forms.HiddenInput())

class FPPCustomForm(forms.Form):
    useless = forms.IntegerField(required=False, widget=forms.HiddenInput())

class BDACustomForm(forms.Form):
    useless = forms.IntegerField(required=False, widget=forms.HiddenInput())

class CandidateForm(forms.Form):
    name = forms.CharField(min_length=1,max_length=140, required=True)

class EmailGuestForm(forms.Form):
    email = forms.EmailField(required=False)

class ElectionForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=140, required=True, label='Name of the poll')
    message = forms.CharField(min_length=0, max_length=1000, label='Message to the voters', required=False, widget=forms.Textarea)
    type = forms.ChoiceField(choices=[(1,'Only guests are allowed to vote. You will invite them by email.'),(2,'You invite people with an url that anyone can use as many times as one wants.')], widget=forms.RadioSelect, required=True, label='Voting mode')
    system = forms.ChoiceField(choices=[(s.key,s.name) for s in System.objects.all()], required=True)

class CreatorForm(forms.Form):
    your_name = forms.CharField(min_length=2, max_length=140, required=True)
    email = forms.EmailField(required=False)

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
    ranking = forms.CharField(max_length=1000, required=True, widget=forms.HiddenInput())

class RGVBallotForm(BallotForm):
    def __init__(self, *args, **kwargs):
        super(RGVBallotForm, self).__init__(*args, **kwargs)
        for choice in self.choices:
            self.fields[choice[0]] = forms.IntegerField(max_value=self.custom['max'], min_value=self.custom['min'],label=choice[1], required=True)