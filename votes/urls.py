from django.contrib import admin
from django.urls import path, include

from .views import ApprovalVoteView, DoneView, ApprovalResultView, HomeView, VoteView, FPTPResultView, FPTPVoteView, \
    STVVoteView, STVResultView, UpdateElection, CreateElection, CreateCandidate, UpdateCandidate, AdminView, TicketView, \
    ResultView, IDTicketView, DateTicketView, STVAllVoteView, AllTicketView, UsernameTicketView, UserTicketView, \
    DeleteTicketView, ResetVoteView, CloseElectionView

app_name = "votes"

urlpatterns = [
    path('', HomeView.as_view(), name="elections"),
    path('<int:election>/', VoteView.as_view(), name="vote"),
    path('<int:election>/approval/',
         ApprovalVoteView.as_view(), name="approval_vote"),
    path('<int:election>/fptp/', FPTPVoteView.as_view(), name="fptp_vote"),
    path('<int:election>/stv/', STVVoteView.as_view(), name="stv_vote"),
    path('<int:election>/<uuid:slug>/', DoneView.as_view(), name="vote_done"),
    path('<int:election>/results/', ResultView.as_view(), name="results"),
    path('<int:election>/results/approval/',
         ApprovalResultView.as_view(), name="approval_results"),
    path('<int:election>/results/fptp/',
         FPTPResultView.as_view(), name="fptp_results"),
    path('<int:election>/results/stv/',
         STVResultView.as_view(), name="stv_results"),
    path('<int:election>/results/stv/votes/',
         STVAllVoteView.as_view(), name="stv_all_votes"),
    path('admin/', AdminView.as_view(), name="admin"),
    path('admin/reset_vote/', ResetVoteView.as_view(), name="reset_vote"),
    path('admin/tickets/', TicketView.as_view(), name="tickets"),
    path('admin/tickets/id', IDTicketView.as_view(), name="tickets_id"),
    path('admin/tickets/date', DateTicketView.as_view(), name="tickets_date"),
    path('admin/tickets/all', AllTicketView.as_view(), name="tickets_all"),
    path('admin/tickets/username',
         UsernameTicketView.as_view(), name="tickets_username"),
    path('admin/tickets/user', UserTicketView.as_view(), name="tickets_user"),
    path('admin/tickets/delete', DeleteTicketView.as_view(), name="tickets_delete"),
    path('admin/create/', CreateElection.as_view(), name="create_election"),
    path('admin/edit/<int:election>/',
         UpdateElection.as_view(), name="update_election"),
    path('admin/edit/<int:election>/create/',
         CreateCandidate.as_view(), name="create_candidate"),
    path('admin/edit/<int:election>/edit/<int:candidate>/',
         UpdateCandidate.as_view(), name="update_candidate"),
    path('admin/close_all/', CloseElectionView.as_view(), name="close"),
]
