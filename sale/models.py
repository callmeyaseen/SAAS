from django.db import models
from django.core.exceptions import ValidationError
from utilities.models import Product, Yarn


class SaleOrder(models.Model):
    sale_order_no = models.CharField(max_length=50, unique=True)
    so_date = models.DateField()

    customer_po_no = models.CharField(max_length=50, blank=True, null=True)
    customer_po_date = models.DateField(blank=True, null=True)

    category = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)

    # 👇 UPDATED PART
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    yarn = models.ForeignKey(Yarn, on_delete=models.CASCADE, null=True, blank=True)

    order_qty = models.FloatField()
    fabric_width_type = models.CharField(max_length=20)
    fabric_width = models.FloatField()

    unit = models.CharField(max_length=20)
    finishing_process = models.CharField(max_length=200)

    cut_level = models.CharField(max_length=10)
    sample_status = models.CharField(max_length=10)
    received_by = models.CharField(max_length=50)

    shipment_location = models.CharField(max_length=200)
    delivery_date = models.DateField()

    order_type = models.CharField(max_length=50)
    payment_term = models.CharField(max_length=50)

    price_order = models.FloatField()
    rate = models.FloatField()

    currency_type = models.CharField(max_length=10)
    currency_rate = models.FloatField()

    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Open") # Open / Closed

    def clean(self):
        # ❗ validation: sirf ek select hona chahiye
        if not self.product and not self.yarn:
            raise ValidationError("Select either Product or Yarn")

        if self.product and self.yarn:
            raise ValidationError("Select only one: Product or Yarn")

    def __str__(self):
        return self.sale_order_no