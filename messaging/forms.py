from crispy_forms.helper import *
from django import forms
from django.forms import ValidationError, formset_factory
from django.urls import reverse_lazy

import re

from users.models import Member
from .utils import visible

MD_INPUT = {
    'class': 'markdown-input',
    'data-endpoint': reverse_lazy('utilities:preview'),
    'rows': '3',
}


class Respond(forms.Form):
    message = forms.CharField(
        label="Message", widget=forms.Textarea(attrs=MD_INPUT))

    def clean_message(self):
        # print("clean_message")
        if re.match(r'^\s*$', visible(self.cleaned_data['message'])):
            raise ValidationError('Message has no content')
        return self.cleaned_data['message']


class Confirm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())


class QuickDM(forms.Form):
    recipient = forms.CharField(label="Recipient", max_length=100,
                                widget=forms.TextInput(attrs={'class': 'add-member-input',
                                                              'autocomplete': 'off'}))
    message = forms.CharField(
        label="Message", widget=forms.Textarea(attrs=MD_INPUT))

    def clean_recipient(self):
        try:
            recipient = Member.objects.get(
                equiv_user__username__iexact=self.cleaned_data['recipient'])
        except Member.DoesNotExist:
            raise ValidationError('Recipient with that username not found')
        return recipient

    def clean_message(self):
        # print("clean_message")
        if re.match(r'^\s*$', visible(self.cleaned_data['message'])):
            raise ValidationError('Message has no content')
        return self.cleaned_data['message']


class MemberForm(forms.Form):
    recipient = forms.CharField(label="Recipient", max_length=100,
                                widget=forms.TextInput(attrs={'class': 'add-member-input',
                                                              'autocomplete': 'off'}))

    def clean_recipient(self):
        try:
            member = Member.objects.get(
                equiv_user__username__iexact=self.cleaned_data['recipient'])
        except Member.DoesNotExist:
            raise ValidationError('User with that username not found')
        return member


MemberFormset = formset_factory(MemberForm, extra=3)
