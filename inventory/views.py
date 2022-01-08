from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.mixins import PermissionRequiredMixin as PRMBase
from django.contrib import messages

from django.shortcuts import get_object_or_404, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.views import redirect_to_login

from notifications.models import NotifType
from notifications.utils import notify, notify_bulk
from users.models import Member
from users.achievements import give_achievement_once
from users.permissions import PERMS
from .forms import SuggestionForm, LoanRequestForm, LoanSurrogateRequestForm, RecordForm, LoanNotesForm
from .models import Inventory, Loan, Record, Suggestion


class PermissionRequiredMixin(PRMBase):
    def handle_no_permission(self):
        messages.add_message(self.request, messages.ERROR,
                             "You don't have permission to perform that action.")
        if self.raise_exception or self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse("homepage"))
        return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())


# Create your views here.
class ListAllInventory(ListView):
    model = Loan
    template_name = "inventory/all_inventory.html"

    def get_queryset(self):
        inv = get_object_or_404(Inventory, name__iexact=self.kwargs['inv'])
        if 'name' in self.request.GET:
            return Record.objects.filter(inventory=inv, name__icontains=self.request.GET['name'])
        else:
            return Record.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, name__iexact=self.kwargs['inv'])
        return ctxt


class RecordDetail(DetailView):
    model = Record
    template_name = "inventory/record_detail.html"

    def get_queryset(self):
        inv = get_object_or_404(Inventory, name__iexact=self.kwargs['inv'])
        return Record.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, name__iexact=self.kwargs['inv'])
        return ctxt


# Create your views here.
class ListAllLoans(LoginRequiredMixin, ListView):
    model = Loan
    template_name = "inventory/all_loans.html"

    def get_queryset(self):
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        if self.request.user.has_perm(PERMS.inventory.view_loan):
            return Loan.objects.filter(inventory=inv)
        else:
            return Loan.objects.filter(inventory=inv, requester=self.request.user.member)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return ctxt


class LoanDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Loan
    template_name = "inventory/loan_detail.html"

    def test_func(self):
        object = get_object_or_404(Loan, pk=self.kwargs['pk'])
        return ((object.requester == self.request.user.member) or
                self.request.user.has_perm(PERMS.inventory.view_loan))

    def get_queryset(self):
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        return Loan.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return ctxt


# Create your views here.
class ListAllSuggestions(ListView):
    model = Suggestion
    template_name = "inventory/all_suggestions.html"

    def get_queryset(self):
        inv = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        if 'archived' in self.request.GET and self.request.GET['archived']:
            suggestions = Suggestion.objects.filter(inventory=inv)
        else:
            suggestions = Suggestion.objects.filter(
                inventory=inv, archived=False)
        if 'name' in self.request.GET:
            return suggestions.filter(name__icontains=self.request.GET['name'])
        else:
            return suggestions

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return ctxt


class SuggestionDetail(DetailView):
    model = Suggestion
    template_name = "inventory/suggestion_detail.html"

    def get_queryset(self):
        inv = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return Suggestion.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return ctxt


class CreateSuggestion(LoginRequiredMixin, CreateView):
    model = Suggestion
    form_class = SuggestionForm
    template_name = "inventory/edit_suggestion.html"

    def get_queryset(self):
        inv = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return Record.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return ctxt

    def form_valid(self, form):
        form.instance.requester = self.request.user.member
        form.instance.inventory = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        give_achievement_once(self.request.user.member,
                              "suggested_game", request=self.request)
        return super().form_valid(form)


class UpdateSuggestion(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Record
    form_class = SuggestionForm
    template_name = "inventory/edit_suggestion.html"

    def test_func(self):
        return (self.request.user.member == self.object.requester or
                self.request.user.has_perm(PERMS.inventory.change_suggestion))

    def get_queryset(self):
        inv = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return Record.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, suggestions=True, name__iexact=self.kwargs['inv'])
        return ctxt


class UpdateRecord(PermissionRequiredMixin, UpdateView):
    model = Record
    form_class = RecordForm
    template_name = "inventory/edit_record.html"
    permission_required = PERMS.inventory.change_record

    def get_queryset(self):
        inv = get_object_or_404(Inventory, name__iexact=self.kwargs['inv'])
        return Record.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, name__iexact=self.kwargs['inv'])
        return ctxt


class CreateRecord(PermissionRequiredMixin, CreateView):
    model = Suggestion
    form_class = RecordForm
    template_name = "inventory/edit_record.html"
    permission_required = PERMS.inventory.add_record

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        inv = get_object_or_404(Inventory, name__iexact=self.kwargs['inv'])
        ctxt['inv'] = inv
        return ctxt

    def form_valid(self, form):
        form.instance.inventory = get_object_or_404(
            Inventory, name__iexact=self.kwargs['inv'])
        return super().form_valid(form)


class UpdateLoan(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Loan
    form_class = LoanRequestForm
    template_name = "inventory/edit_loan.html"

    def test_func(self):
        object = get_object_or_404(Loan, pk=self.kwargs['pk'])
        return ((object.requester == self.request.user.member and object.can_edit()) or
                self.request.user.has_perm(PERMS.inventory.change_loan))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'inv_': get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])})
        return kwargs

    def get_queryset(self):
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        return Loan.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return ctxt


class NotateLoan(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanNotesForm
    template_name = "inventory/edit_loan.html"
    permission_required = PERMS.inventory.change_loan

    def get_queryset(self):
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        return Loan.objects.filter(inventory=inv)

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt['inv'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return ctxt


class CreateLoan(LoginRequiredMixin, CreateView):
    model = Loan
    form_class = LoanRequestForm
    template_name = "inventory/edit_loan.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['inv_'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return kwargs

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        ctxt['inv'] = inv
        return ctxt

    def form_valid(self, form):
        form.instance.inventory = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        form.instance.requester = self.request.user.member
        response = super().form_valid(form)
        notify_bulk(Member.users_with_perm(PERMS.inventory.view_loan), NotifType.LOAN_REQUESTS,
                    f"A new loan has been requested by {self.request.user.username}.",
                    reverse('inventory:loan_detail',
                            kwargs={'inv': self.object.inventory.canonical_(), 'pk': self.object.id}),
                    merge_key=self.object.id)
        return response


class CreateSurrogateLoan(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Loan
    form_class = LoanSurrogateRequestForm
    template_name = "inventory/edit_loan.html"
    permission_required = PERMS.inventory.can_surrogate

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['inv_'] = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])
        return kwargs

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        inv = get_object_or_404(Inventory, loans=True,
                                name__iexact=self.kwargs['inv'])
        ctxt['inv'] = inv
        return ctxt

    def form_valid(self, form):
        form.instance.inventory = get_object_or_404(
            Inventory, loans=True, name__iexact=self.kwargs['inv'])

        response = super().form_valid(form)

        notify_bulk(Member.users_with_perm(PERMS.inventory.view_loan), NotifType.LOAN_REQUESTS,
                    f"A new loan has been requested for {form.instance.requester.username} by {self.request.user.username}.",
                    reverse('inventory:loan_detail',
                            kwargs={'inv': self.object.inventory.canonical_(), 'pk': self.object.id}),
                    merge_key=self.object.id)

        notify(form.instance.requester, NotifType.LOAN_REQUESTS,
               f"A loan request has been created for you by {self.request.user.username}.",
               reverse('inventory:loan_detail',
                       kwargs={'inv': self.object.inventory.canonical_(), 'pk': self.object.id}))

        return response
