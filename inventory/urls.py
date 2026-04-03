from django.urls import path
from . import views

urlpatterns = [
    path("mpr-entry/", views.mpr_entry, name="mpr_entry"),
    path("mpr-list/", views.mpr_list, name="mpr_list"),
    path("mpr-report/<str:mpr_no>/", views.mpr_report, name="mpr_report"),
]