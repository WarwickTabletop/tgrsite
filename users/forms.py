from django.contrib.auth.models import User
from django.db.models import TextChoices
from django.forms import ModelForm, Textarea, TextInput, CharField, HiddenInput, EmailInput, PasswordInput, ChoiceField

from django.forms import ValidationError, Form, RadioSelect
from django.utils.safestring import mark_safe
from django.core import validators

from notifications.models import NotificationTemplates
from .models import Member
from .captcha import check_signed_captcha

BOOTSTRAP_FORM_WIDGET_attrs = {
    'class': 'form-control'
}

MD_INPUT = {
    'class': 'markdown-input'
}


class UniIDForm(Form):
    uni_id = CharField(max_length=8, validators=[validators.RegexValidator(r'^u?[0-9]{7}$')],
                       help_text="Enter your University ID", label="University ID",
                       widget=TextInput(attrs={"placeholder": "u0000000"}))


class LoginForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': TextInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs),
            'password': PasswordInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs),
        }


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

        # they all have the same format (TextInputs)
        widgets = {
            i: TextInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs) for i in fields
        }
        # ...except this one
        widgets['email'] = EmailInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs)

        help_texts = {
            'first_name': "Please consider adding your name to help others recognise you"
        }

    def clean(self):
        data = self.cleaned_data
        if 'username' not in data:
            raise ValidationError('')

        if len(data['username']) > 32:
            self.add_error('username', ValidationError(
                'Username must be 32 characters or fewer.'))


class SignupForm(ModelForm):
    notification = ChoiceField(choices=NotificationTemplates.choices, required=True,
                               help_text="These can be customised from your profile after signup.",
                               label="Initial Email Preferences", widget=RadioSelect())
    captcha = CharField(
        max_length=32, label="Something went wrong generating a captcha. Please contact the web admin")
    captcha_token = CharField(widget=HiddenInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

        widgets = {
            'password': PasswordInput()
        }

        help_texts = {
            'username': 'Required. 32 characters or fewer. Letters, digits and @/./+/-/_ only.'
        }

    def clean(self):
        if 'captcha' not in self.cleaned_data or 'captcha_token' not in self.cleaned_data:
            self.add_error('captcha', "Invalid Captcha Answer")
            return None
        captcha = self.cleaned_data['captcha']
        captcha_token = self.cleaned_data['captcha_token']
        if not check_signed_captcha(captcha, captcha_token):
            self.add_error('captcha', "Invalid Captcha Answer")
            return None
        return self.cleaned_data

    def clean_username(self):
        if len(self.cleaned_data['username']) > 32:
            raise ValidationError('Username must be 32 characters or fewer.')
        if User.objects.filter(username__iexact=self.cleaned_data['username']).exists():
            raise ValidationError('Username already exists.')
        return self.cleaned_data['username']


class MemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ['discord', 'pronoun', 'bio',
                  'signature', 'official_photo_url', 'dark']

        widgets = {
            'discord': TextInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs),
            'pronoun': TextInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs),
            'bio': Textarea(attrs=MD_INPUT),
            'signature': Textarea(attrs=MD_INPUT),
            'official_photo_url': TextInput(attrs=BOOTSTRAP_FORM_WIDGET_attrs)
        }

        help_texts = {
            'official_photo_url': mark_safe(
                'Provide a URL for a real photo of you. '
                'This is only shown on the exec page and only if you are a member of exec! '
                'Gravatar is used by the rest of the site for profile pictures - for more information see this '
                '<a href="https://github.com/WarwickTabletop/tgrsite/wiki/Gravatar">guide</a>.'),
            'discord': 'Add your discord ID to aid recognition on the society discord',
            'pronoun': 'Please add your pronouns to allow other members know how to refer to you'
        }
