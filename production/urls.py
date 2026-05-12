from django.urls import path
from . import views

app_name = "production"

urlpatterns = [
    path('', views.plan_list, name='plan_list'),
    path('create/', views.plan_create, name='plan_create'),
    path('detail/<int:pk>/', views.plan_detail, name='plan_detail'),
    path('edit/<int:pk>/', views.plan_edit, name='plan_edit'),
    path('delete/<int:pk>/', views.plan_delete, name='plan_delete'),
    path('get-so-details/<int:pk>/', views.get_so_details, name='get_so_details'),
    path('get-wo-details/<int:pk>/', views.get_wo_details, name='get_wo_details'),
    path('get-machine-load/', views.get_machine_load, name='get_machine_load'),
    path('scan-roll/', views.scan_roll, name='scan_roll'),
    path('roll-edit/<int:pk>/', views.roll_edit, name='roll_edit'),
    path('scan/', views.plan_scan, name='plan_scan'),
    path('get-next-roll/<str:plan_no>/', views.get_next_roll, name='get_next_roll'),
    path('roll-delete/<int:pk>/', views.roll_delete, name='roll_delete'),
    path('get-machine-plans/<str:code>/', views.get_machine_plans, name='get_machine_plans'),
    path('create-wo/', views.create_wo, name='create_wo'),
    path('wo-list/', views.wo_list, name='wo_list'),
    path('wo-view/<int:pk>/', views.wo_detail, name='wo_detail'),
]