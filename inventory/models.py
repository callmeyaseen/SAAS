from django.db import models
from django.contrib.auth.models import User
from utilities.models import Yarn
from core.models import AuditModel
# ================= MPR HEADER =================
class MPR(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    mpr_no = models.CharField(max_length=20, unique=True)
    mpr_date = models.DateField(auto_now_add=True)
    req_type = models.CharField(max_length=50, default="Stock")
    request_from = models.CharField(max_length=100)
    # department = models.CharField(max_length=100)
    department = models.ForeignKey('utilities.Department',on_delete=models.SET_NULL,null=True,blank=True)
    priority = models.CharField(max_length=50, default="Normal")
    required_date = models.DateField()
    remarks = models.TextField(blank=True)
    # OPTIONAL vendor suggestion (useful for PO auto fill)
    suggested_vendor = models.ForeignKey('utilities.Vendor',on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="Pending")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.mpr_no

# ================= MPR ITEM DETAIL =================
class MPRItem(models.Model):
    mpr = models.ForeignKey(MPR,on_delete=models.CASCADE,related_name="items")
    item = models.ForeignKey(Yarn,on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10,decimal_places=2)
    rate = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    # remaining qty for PO tracking
    remaining_qty = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        if not self.remaining_qty:
            self.remaining_qty = self.quantity
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.item} - {self.quantity}"
    
