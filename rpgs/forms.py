from django import forms
from django.forms import Textarea, CharField, NumberInput

import re

from .models import Rpg, Tag

MD_INPUT = {
    'class': 'markdown-input'
}

splitter = re.compile('[|:;,]')


class RpgForm(forms.ModelForm):
    tag_list = CharField(required=False, help_text="A list of tags separated by commas. "
                                                   "Please remember to add 'rpg' to any rpgs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and ('tag_list' not in self.initial or not self.initial['tag_list']):
            self.initial['tag_list'] = self.instance.tags_str()
            self.fields['tag_list'].value = self.instance.tags_str()

    class Meta:
        model = Rpg
        fields = ['title', 'system', 'description', 'players_wanted',
                  'timeslot', 'location', 'is_in_the_past', 'finishes']
        widgets = {
            'description': Textarea(attrs=MD_INPUT),
        }

    def clean_tag_list(self):
        tags = self.cleaned_data['tag_list']
        tags = {x.strip().lower() for x in splitter.split(tags)}
        if '' in tags:
            tags.remove('')
        if tags and len(max(tags, key=len)) > 40:
            raise forms.ValidationError("Tag too long")
        return tags


class RpgCreateForm(RpgForm):
    class Meta:
        model = Rpg
        fields = ['title', 'system', 'description', 'players_wanted',
                  'timeslot', 'location', 'finishes', 'published']
        widgets = {
            'description': Textarea(attrs=MD_INPUT),
        }
