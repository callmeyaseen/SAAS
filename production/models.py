from django.db import models
from sale.models import SaleOrder
from utilities.models import Machine   # assume tu ne machine app banayi hai


class ProductionPlan(models.Model):

    plan_no = models.CharField(max_length=50, unique=True)

    sale_order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE)

    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True)

    planned_qty = models.FloatField()

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=20, default="Open") # Open / Closed

    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.plan_no

class ProductionRoll(models.Model):
    plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='rolls')
    roll_no = models.CharField(max_length=100, unique=True)
    weight = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.roll_no
