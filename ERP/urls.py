from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views
from dashboard import views as dashboard_views

urlpatterns = [

    # ROOT URL → LOGIN PAGE
    path("", account_views.user_login, name="login"),

    # ADMIN
    path("admin/", admin.site.urls),

    # APPS
    path('', dashboard_views.home, name='home'),
    path("dashboard/", include("dashboard.urls")),
    path("utilities/", include("utilities.urls")),
    path("accounts/", include("accounts.urls")),
    path("inventory/", include("inventory.urls")),
    path('purchasing/', include('purchasing.urls')),
    path('sale/', include('sale.urls'))
]