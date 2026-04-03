from django.db import models
from django.contrib.auth.models import User
from inventory.models import Yarn
from utilities.models import Vendor


# ================= PURCHASE ORDER =================
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    po_no = models.CharField(max_length=20,unique=True,blank=True)
    supplier = models.ForeignKey('utilities.Vendor',on_delete=models.CASCADE)
    # MPR LINK
    mpr = models.ForeignKey('inventory.MPR',on_delete=models.SET_NULL,null=True,blank=True)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')

    # ================= USERS =================
    prepared_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name="po_prepared")
    approved_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="po_approved")
    rejected_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="po_rejected")
    approved_date = models.DateTimeField(null=True,blank=True)
    rejected_date = models.DateTimeField(null=True,blank=True)
    reject_reason = models.TextField(blank=True)
    # ================= AUTO PO NUMBER =================
    def save(self, *args, **kwargs):

        if not self.po_no:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            if last_po and last_po.po_no:
                try:
                    number = int(last_po.po_no.split('-')[1]) + 1
                except:
                    number = 1
            else:
                number = 1
            self.po_no = f"PO-{number:04d}"
        super().save(*args, **kwargs)
    def __str__(self):
        return self.po_no
# ================= PURCHASE ORDER ITEMS =================
class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder,related_name='items',on_delete=models.CASCADE)
    item = models.ForeignKey('utilities.Yarn',on_delete=models.CASCADE)
    # MPR QUANTITY
    mpr_quantity = models.FloatField()
    # PO QUANTITY
    quantity = models.FloatField()
    rate = models.FloatField()
    # ================= AMOUNT =================
    @property
    def amount(self):
        return self.quantity * self.rate
    def __str__(self):
        return f"{self.item} - {self.quantity}"   
# ================= CREATE GRN =================
class GRN(models.Model):
    grn_no = models.CharField(max_length=20, unique=True)
    po = models.ForeignKey("PurchaseOrder",on_delete=models.CASCADE)
    supplier = models.ForeignKey(Vendor,on_delete=models.CASCADE)
    received_date = models.DateField()
    received_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.grn_no
#  ================= GRN ITEMS =================
class GRNItem(models.Model):
    grn = models.ForeignKey(GRN,related_name="items",on_delete=models.CASCADE)
    item = models.ForeignKey(Yarn,on_delete=models.CASCADE)
    po_qty = models.DecimalField(max_digits=10,decimal_places=2)
    received_qty = models.DecimalField(max_digits=10,decimal_places=2)
    remarks = models.CharField(max_length=200,blank=True)
    
# ================= Inventory Model =================
class Stock(models.Model):

    item = models.ForeignKey("utilities.Yarn", on_delete=models.CASCADE)

    rack = models.ForeignKey("utilities.Rack", on_delete=models.CASCADE, null=True, blank=True  )

    quantity = models.FloatField(default=0)

    updated_at = models.DateTimeField(auto_now=True)