import requests
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.messages import add_message
from django.contrib.messages import constants as messages
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, View, DetailView, TemplateView

from forum.models import Thread, Response
from rpgs.models import Rpg
from .captcha import create_signed_captcha
from .forms import MemberForm, UserForm, SignupForm, UniIDForm
from .models import Member, Membership, VerificationRequest, Achievement
from .utils import sendRequestMailings, getApiMembers
from .achievements import age_achievements, give_achievement, give_achievement_once


def get_achievements_with_merged(object):
    # Note: may contain duplicates.
    achievements = object.achievementaward_set.order_by('-achieved_at')
    mapping = {}
    result = []
    for achiev in achievements:
        key = achiev.achievement.name
        if key in mapping:
            result[mapping[key]]['achieved_at'].append(achiev.achieved_at)
        else:
            mapping[key] = len(result)
            result.append({'achievement': achiev.achievement, 'achieved_at': [achiev.achieved_at]})
    return result


class ProfileView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "users/view.html"
    context_object_name = "member"

    def get_queryset(self):
        return Member.objects.filter(equiv_user__is_active=True)

    def get_context_data(self, **kwargs):
        pk = self.object.pk
        ctxt = super().get_context_data(**kwargs)
        achievements = get_achievements_with_merged(self.object)
        ctxt.update({'recent_threads': Thread.objects.filter(author__id=pk).order_by('-pub_date')[:3],
                     'recent_responses': Response.objects.filter(author__id=pk).order_by('-pub_date')[:3],
                     'rpgs': Rpg.objects.visible(self.request.user.member).filter(game_masters__id=pk, is_in_the_past=False)
                        .order_by('published', '-pinned', '-created_at')[:10],
                     'achievements': achievements[:5],
                     'achievement_count': len(achievements),
                     'achievement_total': Achievement.objects.filter(is_fair=True).count()})
        return ctxt


class MyProfile(ProfileView):
    def get_object(self, queryset=None):
        return self.request.user.member


class Edit(LoginRequiredMixin, View):
    # TODO use a more generic view for this, FormProcessMixin like behaviour perhaps?

    def get(self, request):
        context = {
            # I want ultimately to get request.user to return member, this is convoluted to prevent this breaking
            'userform': UserForm(instance=request.user.member.equiv_user),
            'memberform': MemberForm(instance=request.user.member),
        }
        return render(request, 'users/edit.html', context)

    def post(self, request):
        # generate a filled form from the post request
        memberform = MemberForm(request.POST, instance=request.user.member)
        userform = UserForm(request.POST, instance=request.user)
        if memberform.is_valid() & userform.is_valid():
            memberform.save()
            userform.save()
            add_message(request, messages.SUCCESS, "Profile successfully updated.")
            if request.POST["discord"]:
                give_achievement_once(request.user.member, "discord", request=request)
            if request.POST["pronoun"]:
                give_achievement_once(request.user.member, "pronoun", request=request)
            return HttpResponseRedirect(reverse('users:me'))
        else:
            context = {
                'userform': userform,
                'memberform': memberform,
            }
            return render(request, 'users/edit.html', context)


class Login(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True  # A very slight privacy risk. Negligible for our site...

    def form_valid(self, form):
        add_message(self.request, messages.SUCCESS, "Successfully logged in!")
        return super().form_valid(form)

    def get_success_url(self):
        age_achievements(self.request.user.member)
        return super().get_success_url()


class Logout(LogoutView):
    next_page = reverse_lazy("homepage")

    def get_next_page(self):
        add_message(self.request, messages.SUCCESS, "Successfully logged out!")
        return super().get_next_page()


class ChangePassword(PasswordChangeView):
    def get_success_url(self):
        add_message(self.request, messages.SUCCESS, "Password Changed")
        return reverse("users:me")


class PasswordResetConfirm(PasswordResetConfirmView):
    def get_success_url(self):
        add_message(self.request, messages.SUCCESS, "Password Reset Successfully")
        return reverse("users:login")


class PasswordReset(PasswordResetView):
    html_email_template_name = "registration/password_reset_html_email.html"

    def get_success_url(self):
        return reverse("users:password_reset_done")


class Signup(FormView):
    form_class = SignupForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("notifications:quick_newsletter_subscribe")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captcha_question = ""
        self.captcha_token = ""
        self.captcha_help = ""

    def get_initial(self):
        initial = super().get_initial()
        initial['captcha_token'] = self.captcha_token
        return initial

    def get_form(self, form_class=None):
        q, a, h = create_signed_captcha()
        self.captcha_question = q
        self.captcha_token = a
        self.captcha_help = h
        form = super().get_form(form_class)
        form.fields['captcha'].label = self.captcha_question
        form.fields['captcha'].help_text = self.captcha_help
        return form

    def form_valid(self, form):
        spawn_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
        auth = authenticate(self.request, username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
        if auth is None:
            raise RuntimeError("Impossible state reached")
        login(self.request, auth)
        return super().form_valid(form)

    def form_invalid(self, form):
        data = form.data.copy()
        data['captcha_token'] = self.captcha_token
        data['captcha'] = ""
        form.data = data
        return super().form_invalid(form)


class VerifyRequest(LoginRequiredMixin, FormView):
    form_class = UniIDForm
    template_name = "users/membership/verify.html"
    success_url = reverse_lazy("users:edit")

    def form_valid(self, form):
        valid = super().form_valid(form)
        uni_id = form.cleaned_data['uni_id'].lower().lstrip('u')

        members = getApiMembers()
        if uni_id in members:
            if members[uni_id] == "":
                add_message(self.request, messages.SUCCESS,
                            "Unable to send you a verification link. "
                            "Please contact the Web Admin to manually verify your membership.")
            else:
                v = VerificationRequest.objects.create(member=self.request.user.member,
                                                       uni_id=uni_id, uni_email=members[uni_id])

                sendRequestMailings(self.request.user, v.token, v.uni_email)
        else:
            # create a request to a dummy email to prevent leaking membership info
            v = VerificationRequest.objects.create(member=self.request.user.member,
                                                   uni_id='0000000', uni_email='website@warwicktabletop.co.uk')

            sendRequestMailings(self.request.user, v.token, v.uni_email)

        add_message(self.request, messages.SUCCESS,
                    "A verification has been sent to your uni email. "
                    "Please click the link included in that email to verify your membership.")
        return valid


class AllAchievements(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "users/allachievements.html"
    context_object_name = "member"

    def get_queryset(self):
        return Member.objects.filter(equiv_user__is_active=True)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        awards = get_achievements_with_merged(self.object)
        nonachievements = Achievement.objects.exclude(achievementaward__member=self.object).filter(is_hidden=False)
        nonawards = [{"achievement": i} for i in nonachievements]
        achievements = list(awards) + nonawards
        ctxt.update({'achievements': achievements,
                     'achievement_count': len(awards),
                     'achievement_total': Achievement.objects.filter(is_fair=True).count(),
                     'is_yours': self.object == self.request.user.member,
                     'name': self.object.equiv_user.username})
        return ctxt

class MyAchievements(AllAchievements):
    def get_object(self, queryset=None):
        return self.request.user.member


class VerifyConfirm(View):
    def get(self, request):
        try:
            v = VerificationRequest.objects.get(datetime__gte=timezone.now() - timezone.timedelta(hours=2),
                                                token__exact=self.request.GET['token'])
            if Membership.objects.filter(uni_id=v.uni_id).exists():
                v.member.verifications.all().delete()
                add_message(request, messages.ERROR,
                            "Verification Failed. User is already associated with that ID. "
                            "Please contact the web admin if this is not you.")
            else:
                m, _ = Membership.objects.get_or_create(member=v.member)
                m.uni_id = v.uni_id
                m.uni_email = v.uni_email
                m.active = True
                m.verified = True
                m.checked = timezone.now()
                m.save()
                v.member.verifications.all().delete()
                add_message(request, messages.SUCCESS, "You have successfully verified your membership.")
                give_achievement(v.member, "verify_membership", request=request)
        except (VerificationRequest.DoesNotExist, KeyError):
            add_message(request, messages.ERROR, "Verification Failed. Please try again.")
        return HttpResponseRedirect(reverse("users:me"))


class Tutorial(TemplateView):
    template_name = "tutorial.html"

class TutorialDone(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        request.user.member.seen_tutorial = True
        request.user.member.save()
        return HttpResponse()

@login_required
def allmembers(request):
    usernames = [x.username for x in User.objects.filter(is_active=True).order_by('username')]
    return JsonResponse(usernames, safe=False)


# not a view
# properly sets up a user and member
def spawn_user(username, email, password):
    u = User.objects.create_user(username, email, password)
    m = Member.objects.create(equiv_user=u)
    u.member = m
    u.save()
    m.save()
    return u
