from django.urls import path

from . import views
from . import views_api as api

app_name = "inventory"
urlpatterns = [
    path('<str:inv>/', views.ListAllInventory.as_view(), name='index'),
    path('<str:inv>/<int:pk>/', views.RecordDetail.as_view(), name='item_detail'),
    # path('<str:inv>/<int:pk>/borrow/', views.Createloan.as_view(), name='create_loan'),
    path('<str:inv>/new/', views.CreateRecord.as_view(), name='create_record'),
    path('<str:inv>/<int:pk>/edit/',
         views.UpdateRecord.as_view(), name='edit_record'),
    path('<str:inv>/suggestions/new/',
         views.CreateSuggestion.as_view(), name='create_suggestion'),
    path('<str:inv>/suggestions/',
         views.ListAllSuggestions.as_view(), name='list_suggestions'),
    path('<str:inv>/suggestions/<int:pk>/',
         views.SuggestionDetail.as_view(), name='suggestion_detail'),
    path('<str:inv>/suggestions/<int:pk>/edit/',
         views.CreateSuggestion.as_view(), name='edit_suggestion'),
    path('<str:inv>/borrow/new/', views.CreateLoan.as_view(), name='create_loan'),
    path('<str:inv>/borrow/new/surrogate/',
         views.CreateSurrogateLoan.as_view(), name='create_surrogate_loan'),
    path('<str:inv>/borrow/', views.ListAllLoans.as_view(), name='list_loans'),
    path('<str:inv>/borrow/<int:pk>/',
         views.LoanDetail.as_view(), name='loan_detail'),
    path('<str:inv>/borrow/<int:pk>/edit/',
         views.UpdateLoan.as_view(), name='edit_loan'),
    path('<str:inv>/borrow/<int:pk>/note/',
         views.NotateLoan.as_view(), name='notate_loan'),

    path('api/archive_request/<int:pk>/',
         api.archiveSuggestion, name='archive_suggestion'),
    path('api/reject_loan/<int:pk>/', api.rejectLoan, name='reject_loan'),
    path('api/accept_loan/<int:pk>/', api.authoriseLoan, name='authorise_loan'),
    path('api/report_taken/<int:pk>/', api.takeLoan, name='taken_loan'),
    path('api/report_back/<int:pk>/', api.returnLoan, name='returned_loan'),
]
