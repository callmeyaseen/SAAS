from django.contrib import admin
from .models import Vendor, Rack, Yarn


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor_code', 'vendor_name', 'phone', 'email')
    search_fields = ('vendor_name', 'vendor_code', 'phone')


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ('rack_no', 'location')
    search_fields = ('rack_no',)


@admin.register(Yarn)
class YarnAdmin(admin.ModelAdmin):
    list_display = ('yarn_code', 'item_name', 'unit', 'shade', 'yarn_type')
    search_fields = ('yarn_code', 'item_name')