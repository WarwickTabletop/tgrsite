import random
from operator import itemgetter, attrgetter

from django.contrib.messages import add_message
from django.contrib.messages import constants as messages
from django.db import transaction, DatabaseError
from django.shortcuts import render, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, ListView, DetailView, RedirectView, CreateView, UpdateView, \
    FormView
from django.shortcuts import get_object_or_404, HttpResponseRedirect, reverse

from users.permissions import PERMS

from users.models import Membership, Member
from .forms import ElectionForm, CandidateForm, DateTicketForm, IDTicketForm, UsernameTicketForm, AllTicketForm, \
    MemberTicketForm, DeleteTicketForm, ResetVoteForm
from .models import Election, STVVote, STVPreference, FPTPVote, APRVVote, Candidate, Ticket, Vote, STVResult
from .stv import Election as StvCalculator


# Create your views here.
class HomeView(LoginRequiredMixin, ListView):
    template_name = "votes/home.html"
    model = Election
    context_object_name = "elections"

    def get_queryset(self):
        tickets = self.request.user.member.ticket_set.filter()
        return Election.objects.filter(ticket__in=tickets, open=True)

    def get_context_data(self, *args, **kwargs):
        ctxt = super().get_context_data(*args, **kwargs)
        ctxt['tickets'] = self.request.user.member.ticket_set.filter()
        return ctxt


class AdminView(PermissionRequiredMixin, ListView):
    template_name = "votes/admin.html"
    permission_required = PERMS.votes.view_election
    model = Election
    context_object_name = "elections"

    def get_queryset(self):
        return Election.objects.filter(archive=False)

    def get_context_data(self, *args, **kwargs):
        ctxt = super().get_context_data(*args, **kwargs)
        ctxt['open_elections'] = self.get_queryset().filter(open=True)
        ctxt['closed_elections'] = self.get_queryset().filter(
            Q(stvvote__isnull=False) | Q(aprvvote__isnull=False) | Q(fptpvote__isnull=False), open=False)
        return ctxt


class TicketView(PermissionRequiredMixin, TemplateView):
    permission_required = PERMS.votes.add_ticket
    template_name = "votes/ticket.html"


class IDTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.add_ticket
    form_class = IDTicketForm
    template_name = "votes/tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for uniid in form.cleaned_data['ids'].split():
            try:
                membership = Membership.objects.get(uni_id=uniid.lstrip('u'))
                for election in form.cleaned_data['elections']:
                    Ticket.objects.get_or_create(
                        member_id=membership.member_id, election=election)
            except Membership.DoesNotExist:
                pass
        return super().form_valid(form)


class DateTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.add_ticket
    form_class = DateTicketForm
    template_name = "votes/tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for membership in Membership.objects.filter(checked__lte=form.cleaned_data['date'], active=True):
            for election in form.cleaned_data['elections']:
                Ticket.objects.get_or_create(
                    member_id=membership.member_id, election=election)
        return super().form_valid(form)


class DeleteTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.delete_ticket
    form_class = DeleteTicketForm
    template_name = "votes/delete_tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for election in form.cleaned_data['elections']:
            Ticket.objects.filter(election=election).delete()
        return super().form_valid(form)


class AllTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.add_ticket
    form_class = AllTicketForm
    template_name = "votes/tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for member in Member.objects.filter(equiv_user__is_active=True):
            for election in form.cleaned_data['elections']:
                Ticket.objects.get_or_create(
                    member_id=member.id, election=election)
        return super().form_valid(form)


class UsernameTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.add_ticket
    form_class = UsernameTicketForm
    template_name = "votes/tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for username in form.cleaned_data['ids'].split():
            try:
                member = Member.objects.get(
                    equiv_user__username__iexact=username.strip())
                for election in form.cleaned_data['elections']:
                    Ticket.objects.get_or_create(
                        member_id=member.id, election=election)
            except Member.DoesNotExist:
                pass
        return super().form_valid(form)


class UserTicketView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.add_ticket
    form_class = MemberTicketForm
    template_name = "votes/tickets.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        for member in form.cleaned_data['members']:
            for election in form.cleaned_data['elections']:
                Ticket.objects.get_or_create(
                    member_id=member.id, election=election)
        return super().form_valid(form)


class ResetVoteView(PermissionRequiredMixin, FormView):
    permission_required = PERMS.votes.change_ticket
    form_class = ResetVoteForm
    template_name = "votes/reset_vote.html"
    success_url = reverse_lazy('votes:admin')

    def form_valid(self, form):
        uuid = form['uuid']
        ticket = get_object_or_404(Ticket, uuid=uuid)
        if ticket.election.vote_type == Election.Types.FPTP:
            vote = get_object_or_404(FPTPVote, uuid=uuid)
        elif ticket.election.vote_type == Election.Types.STV:
            vote = get_object_or_404(STVVote, uuid=uuid)
        elif ticket.election.vote_type == Election.Types.APRV:
            vote = get_object_or_404(APRVVote, uuid=uuid)
        else:
            raise Http404()
        try:
            with transaction.atomic():
                vote.delete()
                ticket.spent = False
                ticket.save()
        except DatabaseError:
            add_message(self.request, "Unable to delete vote", messages.ERROR)

        return super().form_valid(form)


class CreateElection(PermissionRequiredMixin, CreateView):
    model = Election
    permission_required = PERMS.votes.add_election
    template_name = "votes/create_election.html"
    form_class = ElectionForm

    def get_success_url(self):
        return reverse("votes:admin")


class UpdateElection(PermissionRequiredMixin, UpdateView):
    model = Election
    permission_required = PERMS.votes.change_election
    template_name = "votes/create_election.html"
    form_class = ElectionForm
    pk_url_kwarg = "election"

    def get_success_url(self):
        return reverse("votes:admin")


class CreateCandidate(PermissionRequiredMixin, CreateView):
    model = Candidate
    permission_required = PERMS.votes.add_candidate
    template_name = "votes/create_candidate.html"
    form_class = CandidateForm

    def get_success_url(self):
        return reverse("votes:update_election", args=[self.kwargs['election']])

    def form_valid(self, form):
        form.instance.election = get_object_or_404(
            Election, id=self.kwargs['election'])
        return super().form_valid(form)


class UpdateCandidate(PermissionRequiredMixin, UpdateView):
    model = Candidate
    permission_required = PERMS.votes.change_candidate
    template_name = "votes/create_candidate.html"
    form_class = CandidateForm
    pk_url_kwarg = "candidate"

    def get_success_url(self):
        return reverse("votes:update_election", args=[self.kwargs['election']])

    def get_queryset(self):
        return Candidate.objects.filter(election_id=self.kwargs['election'])


class DoneView(LoginRequiredMixin, DetailView):
    model = Vote
    slug_field = "uuid"

    def get_template_names(self):
        if self.election.vote_type == Election.Types.APRV:
            return "votes/approval_done.html"
        elif self.election.vote_type == Election.Types.FPTP:
            return "votes/fptp_done.html"
        elif self.election.vote_type == Election.Types.STV:
            return "votes/stv_done.html"

    def get_queryset(self):
        self.election = get_object_or_404(Election, id=self.kwargs['election'])
        return self.election.votes()


class VoteView(LoginRequiredMixin, RedirectView):
    def get_object(self):
        return get_object_or_404(Election, id=self.kwargs['election'])

    def get_redirect_url(self, *args, **kwargs):
        election = self.get_object()
        if election.vote_type == Election.Types.APRV:
            return reverse('votes:approval_vote', args=[self.kwargs['election']])
        elif election.vote_type == Election.Types.FPTP:
            return reverse('votes:fptp_vote', args=[self.kwargs['election']])
        elif election.vote_type == Election.Types.STV:
            return reverse('votes:stv_vote', args=[self.kwargs['election']])
        else:
            raise NotImplementedError()


class ResultView(PermissionRequiredMixin, RedirectView):
    permission_required = PERMS.votes.view_election

    def get_object(self):
        return get_object_or_404(Election, id=self.kwargs['election'])

    def get_redirect_url(self, *args, **kwargs):
        election = self.get_object()
        if election.vote_type == Election.Types.APRV:
            return reverse('votes:approval_results', args=[self.kwargs['election']])
        elif election.vote_type == Election.Types.FPTP:
            return reverse('votes:fptp_results', args=[self.kwargs['election']])
        elif election.vote_type == Election.Types.STV:
            return reverse('votes:stv_results', args=[self.kwargs['election']])
        else:
            raise NotImplementedError()


class ApprovalResultView(PermissionRequiredMixin, ListView):
    model = Candidate
    permission_required = PERMS.votes.view_aprvvote
    template_name = "votes/approval_results.html"
    ordering = [Count("aprvvotes_set")]
    context_object_name = "choices"

    def get_queryset(self):
        self.election = get_object_or_404(Election, id=self.kwargs['election'], vote_type=Election.Types.APRV,
                                          open=False)
        return self.election.candidate_set.all()

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['election'] = self.election
        ctxt['choices'] = sorted(
            ctxt['choices'], key=lambda x: -x.votes().count())
        return ctxt


class ApprovalVoteView(UserPassesTestMixin, TemplateView):
    template_name = "votes/approval_votescreen.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        self.election = get_object_or_404(Election, id=self.kwargs['election'], open=True,
                                          vote_type=Election.Types.APRV)
        return self.request.user.member.ticket_set.filter(election=self.election, spent=False).exists()

    def post(self, request, **kwargs):
        self.get_context_data(**kwargs)
        ticket = get_object_or_404(
            request.user.member.ticket_set.all(), election=self.election, spent=False)
        print(request.POST)
        errors = []
        if "selection" not in request.POST:
            errors.append("Please select at least one option")
            selection = []
        else:
            selection = request.POST.getlist("selection")
        if 0 < self.election.max_votes < len(selection):
            errors.append("Too many options selected")
        try:
            selection = [int(s) for s in selection]
        except ValueError:
            errors.append("Invalid option submitted")
        allowed = [a.id for a in self.election.candidate_set.all()]
        for i in selection:
            if i not in allowed:
                errors.append("Unknown option selected")

        if errors:
            return self.get(request, errors=errors)
        else:
            vote = APRVVote(
                uuid=ticket.uuid,
                election=self.election,
            )
            vote.save()
            vote.selection.add(*selection)

            ticket.spent = True
            ticket.save()

            return HttpResponseRedirect(
                reverse("votes:vote_done", kwargs={'election': self.election.id, 'slug': vote.uuid}))

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        self.election = get_object_or_404(Election, id=self.kwargs['election'], open=True,
                                          vote_type=Election.Types.APRV)
        ctxt['election'] = self.election
        ctxt['choices'] = list(self.election.candidate_set.all())
        random.shuffle(ctxt['choices'])
        return ctxt


class FPTPResultView(PermissionRequiredMixin, ListView):
    model = Candidate
    permission_required = PERMS.votes.view_fptpvote
    template_name = "votes/fptp_results.html"
    ordering = [Count("fptpvotes_set")]
    context_object_name = "choices"

    def get_queryset(self):
        self.election = get_object_or_404(Election, id=self.kwargs['election'], vote_type=Election.Types.FPTP,
                                          open=False)
        return self.election.candidate_set.all()

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['election'] = self.election
        ctxt['choices'] = sorted(
            ctxt['choices'], key=lambda x: -x.votes().count())
        return ctxt


class FPTPVoteView(UserPassesTestMixin, TemplateView):
    template_name = "votes/fptp_votescreen.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        self.election = get_object_or_404(Election, id=self.kwargs['election'], open=True,
                                          vote_type=Election.Types.FPTP)
        return self.request.user.member.ticket_set.filter(election=self.election, spent=False).exists()

    def post(self, request, **kwargs):
        self.get_context_data(**kwargs)
        ticket = get_object_or_404(
            request.user.member.ticket_set.all(), election=self.election, spent=False)
        print(request.POST)
        errors = []
        if "selection" not in request.POST:
            errors.append("Please select one option")
            selection = []
        else:
            selection = request.POST.get("selection")
        try:
            selection = int(selection)
        except ValueError:
            errors.append("Invalid option submitted")
        allowed = [a.id for a in self.election.candidate_set.all()]
        if selection not in allowed:
            errors.append("Unknown option selected")

        if errors:
            return self.get(request, errors=errors)
        else:
            vote = FPTPVote(
                uuid=ticket.uuid,
                election=self.election,
                selection_id=selection
            )
            vote.save()

            ticket.spent = True
            ticket.save()

            return HttpResponseRedirect(
                reverse("votes:vote_done", kwargs={'election': self.election.id, 'slug': vote.uuid}))

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        self.election = get_object_or_404(Election, id=self.kwargs['election'], open=True,
                                          vote_type=Election.Types.FPTP)
        ctxt['election'] = self.election
        ctxt['choices'] = list(self.election.candidate_set.all())
        random.shuffle(ctxt['choices'])
        return ctxt


class STVResultView(PermissionRequiredMixin, ListView):
    model = Candidate
    permission_required = PERMS.votes.view_stvvote
    template_name = "votes/stv_results.html"
    context_object_name = "choices"

    def get_queryset(self):
        self.election = get_object_or_404(Election, id=self.kwargs['election'], vote_type=Election.Types.STV,
                                          open=False)
        return self.election.candidate_set.all()

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['election'] = self.election
        try:
            res = self.election.stvresult
        except STVResult.DoesNotExist:
            candidates = set(
                map(attrgetter('id'), self.election.candidate_set.all()))
            withdrawn = set(map(attrgetter('id'), self.election.candidate_set.filter(
                state=Candidate.State.WITHDRAWN)))
            votes = []
            for i in self.election.stvvote_set.all():
                vote = []
                for j in STVPreference.objects.filter(stvvote=i).order_by('order'):
                    vote.append(int(j.candidate_id))
                votes.append(tuple(vote))

            calc = StvCalculator(candidates, votes, self.election.seats)
            calc.withdraw(withdrawn)
            calc.full_election()
            res = STVResult.objects.create(
                election=self.election, full_log="\n".join(calc.fulllog))
            res.save()
            res.winners.add(*Candidate.objects.filter(id__in=calc.winners()))
        ctxt['result'] = res
        return ctxt


class STVVoteView(UserPassesTestMixin, TemplateView):
    template_name = "votes/stv_votescreen.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        self.election = get_object_or_404(
            Election, id=self.kwargs['election'], open=True, vote_type=Election.Types.STV)
        return self.request.user.member.ticket_set.filter(election=self.election, spent=False).exists()

    def post(self, request, **kwargs):
        self.get_context_data(**kwargs)
        ticket = get_object_or_404(
            request.user.member.ticket_set.all(), election=self.election, spent=False)
        print(request.POST)
        errors = []
        allowed = set(a.id for a in self.election.candidate_set.all())

        # Almost all of these errors should never be seen (unless someone is bypassing the js)
        submitted_candidates = set(request.POST.keys())
        # remove csrf token (the only valid non-vote value)
        submitted_candidates.remove('csrfmiddlewaretoken')
        try:
            submitted_candidates = set(map(int, submitted_candidates))
        except ValueError:
            errors.append("Unknown option submitted (non integer key)")
        if submitted_candidates.difference(allowed):
            errors.append("Unknown option submitted (unknown candidate)")
        if allowed.difference(submitted_candidates):
            errors.append("Missing option")

        selection = []
        for i in submitted_candidates:
            selection.append((i, request.POST.get(str(i))))

        print(selection)
        try:
            selection = [(s, int(v)) for s, v in selection if v != ""]
        except ValueError:
            errors.append("Invalid preference (non-integer)")
        for k, v in selection:
            if v not in range(1, len(selection) + 1):
                errors.append("Invalid preference (out of range)")
        if len(selection) != len(set(map(itemgetter(1), selection))):
            errors.append("Invalid preference (repeated)")
        if len(selection) == 0:
            # This one is actually possible
            errors.append("Please select at least one candidate")

        if errors:
            return self.get(request, errors=set(errors), previous=request.POST)
        else:
            vote = STVVote(
                uuid=ticket.uuid,
                election=self.election,
            )
            vote.save()
            for i in selection:
                STVPreference.objects.create(
                    stvvote=vote, candidate_id=i[0], order=i[1])

            ticket.spent = True
            ticket.save()

            return HttpResponseRedirect(
                reverse("votes:vote_done", kwargs={'election': self.election.id, 'slug': vote.uuid}))

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        self.election = get_object_or_404(
            Election, id=self.kwargs['election'], open=True, vote_type=Election.Types.STV)
        ctxt['election'] = self.election
        ctxt['choices'] = list(self.election.candidate_set.all())
        random.shuffle(ctxt['choices'])
        return ctxt


class STVAllVoteView(PermissionRequiredMixin, ListView):
    model = Candidate
    permission_required = PERMS.votes.view_stvvote
    template_name = "votes/stv_vote_list.html"
    context_object_name = "choices"

    def get_queryset(self):
        self.election = get_object_or_404(Election, id=self.kwargs['election'], vote_type=Election.Types.STV,
                                          open=False)
        return self.election.candidate_set.all()

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['election'] = self.election
        return ctxt


def maybeint(string):
    try:
        return int(string)
    except ValueError:
        return None
