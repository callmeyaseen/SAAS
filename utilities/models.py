from django.db import models
from core.models import AuditModel
from django.contrib.auth.models import User
def generate_vendor_code():
    last_vendor = Vendor.objects.order_by('id').last()
    if last_vendor:
        return f"VEN-{last_vendor.id + 1:05d}"
    return "VEN-00001"


class Vendor(models.Model):
    vendor_code = models.CharField(max_length=20,unique=True,blank=True, default=generate_vendor_code)
    vendor_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    def __str__(self):
        return self.vendor_name
    
# ================= Racl Model =====================

# ✅ RACK ENTRY (FORM)
class Rack(models.Model):
    rack_no = models.CharField(max_length=20)
    location = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        user = self.created_by.username if self.created_by else "Unknown"
        return f"{user} - {self.rack_no}"

# ================= YARN =================
class Yarn(AuditModel):
    yarn_code = models.CharField(max_length=20, unique=True)
    item_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50)
    shade = models.CharField(max_length=100, blank=True)
    yarn_type = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return f"{self.item_name} ({self.yarn_code})"


# ================= Department =================
class Department(models.Model):

    TYPE_CHOICES = [
        ('Production', 'Production'),
        ('Stock', 'Stock'),
    ]

    name = models.CharField(max_length=100)
    department_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.department_type})"