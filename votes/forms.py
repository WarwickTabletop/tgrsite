from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, Textarea, DateField, ModelMultipleChoiceField, SelectDateWidget, CharField, \
    UUIDField
from django.urls import reverse_lazy

from users.models import Member
from .models import Election, Candidate, Ticket

MD_INPUT_SAFE = {
    'class': 'markdown-input',
    'data-endpoint': reverse_lazy('utilities:preview_safe'),
}

MD_INPUT_TEXT = {
    'class': 'markdown-input',
    'data-endpoint': reverse_lazy('utilities:preview_text'),
}


class ElectionForm(ModelForm):
    class Meta:
        model = Election
        fields = ['name', 'description', 'vote_type',
                  'max_votes', 'seats', 'open']
        widgets = {'description': Textarea(attrs=MD_INPUT_SAFE)}


class CandidateForm(ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'description', 'state']
        widgets = {'description': Textarea(attrs=MD_INPUT_TEXT)}


class IDTicketForm(Form):
    ids = CharField(help_text="A list of whitespace separated uni-ids",
                    widget=Textarea(), label="IDs")
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False))


class UsernameTicketForm(Form):
    ids = CharField(help_text="A list of whitespace separated usernames",
                    widget=Textarea(), label="Usernames")
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False))


class AllTicketForm(Form):
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False))


class MemberTicketForm(Form):
    members = ModelMultipleChoiceField(Member.objects.all())
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False))


class DateTicketForm(Form):
    date = DateField(widget=SelectDateWidget(),
                     help_text="Select the date before which their membership should have been verified." + \
                               "Note that this will only select those who are currently members of the society.")
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False))


class DeleteTicketForm(Form):
    elections = ModelMultipleChoiceField(Election.objects.filter(archive=False, open=False))


class ResetVoteForm(Form):
    uuid = UUIDField(label="Ticket UUID")

    def clean_uuid(self):
        uuid_value = self.cleaned_data['uuid']
        if not Ticket.objects.filter(spent=True, uuid=uuid_value).exists():
            raise ValidationError("Incorrect UUID")
        return uuid_value
