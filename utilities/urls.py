from django.urls import path
from . import views

urlpatterns = [
    path('vendor-entry/', views.vendor_entry, name='vendor_entry'),
    path("vendor-list/", views.vendor_list, name="vendor_list"),
    path("rack-entry/", views.rack_entry, name="rack_entry"),
    path('rack-list/', views.rack_list, name='rack_list'),
    path("item-entry/", views.yarn_entry, name="yarn_entry"),
    path("yarn-audit/", views.yarn_filter, name="yarn_filter"),
    path("department-entry/", views.department_entry, name="department_entry"),
    path("department-list/", views.department_list, name="department_list"),
    path("department-detail/<int:id>/", views.department_detail, name="department_detail"),
    path("product-entry/", views.product_entry, name="product_entry"),
    path("product-list/", views.product_list, name="product_list"),
    path('product/view/<str:voucher_no>/', views.product_view, name='product_view'),
    path("recipe/", views.recipe_entry, name="recipe_entry"),
    path('rack-delete/<int:id>/', views.rack_delete, name='rack_delete'),
    path('machine/', views.machine_entry, name='machine'),
    path("machine/action/", views.machine_action, name="machine_action"),
    path('machine-list/', views.machine_list, name='machine_list'),
    path('machine/detail/<str:code>/', views.machine_detail, name='machine_detail'),
    path("customer-entry/", views.customer_entry, name="customer_entry"),
    # Customer URL
    path('customer-entry/',views.customer_entry,name='customer_entry'),

    path('save-customer/',views.save_customer,name='save_customer'),

    path('find-customer/',views.find_customer,name='find_customer'),

    path('view-customer/<int:id>/',views.view_customer,name='view_customer'),

    path('update-customer/<int:id>/',views.update_customer,name='update_customer'),

    path('delete-customer/<int:id>/',views.delete_customer,name='delete_customer'),

]