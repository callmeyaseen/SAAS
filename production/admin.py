from django.contrib import admin
from .models import ProductionPlan, ProductionRoll, QualityEntry, WorkOrder, WorkOrderItem

@admin.register(ProductionPlan)
class ProductionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_no', 'machine', 'planned_qty', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date')
    search_fields = ('plan_no',)

@admin.register(ProductionRoll)
class ProductionRollAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'plan', 'weight', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('roll_no',)

@admin.register(QualityEntry)
class QualityEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_no', 'roll', 'weight', 'status', 'fault_type', 'created_at')
    list_filter = ('status', 'fault_type', 'created_at')
    search_fields = ('entry_no', 'roll__roll_no')
    readonly_fields = ('entry_no', 'created_at')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_no', 'customer', 'status', 'work_order_date')
    list_filter = ('status', 'work_order_date')
    search_fields = ('work_order_no',)

@admin.register(WorkOrderItem)
class WorkOrderItemAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'product', 'yarn', 'unit_qty', 'required_qty')
    search_fields = ('work_order__work_order_no',)

