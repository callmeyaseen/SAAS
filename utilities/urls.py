from django.urls import path
from . import views

urlpatterns = [
    path('vendor-entry/', views.vendor_entry, name='vendor_entry'),
    path("vendor-list/", views.vendor_list, name="vendor_list"),
    path("rack-entry/", views.rack_entry, name="rack_entry"),
    path('rack-list/', views.rack_list, name='rack_list'),
    path("item-entry/", views.yarn_entry, name="yarn_entry"),
    path("yarn-audit/", views.yarn_filter, name="yarn_filter"),
]