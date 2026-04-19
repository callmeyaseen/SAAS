from django.urls import path
from . import views

urlpatterns = [
    # example
    path('', views.production_home, name='production_home'),
]