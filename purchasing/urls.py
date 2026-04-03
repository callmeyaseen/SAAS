from django.urls import path
from . import views
urlpatterns = [
    path('', views.po_list, name='po_list'),
    path('create/', views.create_po, name='create_po'),
    path('<int:pk>/', views.po_detail, name='po_detail'),
    path('<int:pk>/edit/', views.update_po, name='update_po'),
    path('<int:pk>/delete/', views.delete_po, name='delete_po'),
    path('<int:pk>/approve/', views.approve_po, name='approve_po'),
    path('<int:pk>/reject/', views.reject_po, name='reject_po'),
    path('<int:pk>/reopen/', views.reopen_po, name='reopen_po'),
    path('approvals/', views.po_approval_list, name='po_approval_list'),
    path("get-po-items/<int:po_id>/", views.get_po_items, name="get_po_items"),
    path("create-grn/", views.create_grn, name="create_grn"),
    path("grn-list/", views.grn_list, name="grn_list"),
    path("stock/", views.stock_list, name="stock_list"),
]