from django.contrib import admin
from .models import Role, Module, Permission

admin.site.register(Role)
admin.site.register(Module)
admin.site.register(Permission)