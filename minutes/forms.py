from django.forms import ModelForm, Textarea, ChoiceField
from django.urls import reverse_lazy
from django.utils.functional import lazy

from .models import Meeting, Folder

MD_INPUT = {
    'class': 'markdown-input',
    'data-endpoint': reverse_lazy('utilities:preview_newsletter'),
}


def sorted_folders():
    return sorted([(x.pk, str(x)) for x in Folder.objects.all()], key=lambda x: x[1])


class MeetingForm(ModelForm):
    folder = ChoiceField(choices=sorted_folders)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Meeting
        fields = ['name', 'folder', 'title', 'body', 'date']
        widgets = {
            'body': Textarea(attrs=MD_INPUT),
        }

    def clean_folder(self):
        return Folder.objects.get(pk=self.cleaned_data['folder'])
