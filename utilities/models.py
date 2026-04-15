from django.db import models   
from core.models import AuditModel
from django.contrib.auth.models import User
from django.utils.timezone import now
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
    
# ================= Racl Model =====================

class Rack(models.Model):
    rack_no = models.CharField(max_length=20)
    # department = models.ForeignKey(Department, on_delete=models.CASCADE)
    department = models.ForeignKey("Department", on_delete=models.CASCADE , null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['rack_no', 'department']   # 🔥 DUPLICATE CONTROL

    def __str__(self):
        return f"{self.department} - {self.rack_no}"
# ================= YARN =================
class Yarn(AuditModel):
    yarn_code = models.CharField(max_length=20, unique=True)
    item_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50)
    shade = models.CharField(max_length=100, blank=True)
    yarn_type = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return f"{self.item_name} ({self.yarn_code})"



# Product Model
class Product(models.Model):

    # voucher number store karega
    voucher_no = models.CharField(max_length=50)

    # product name
    product_name = models.CharField(max_length=200, unique=True)

    # department foreign key (relation)
    department = models.ForeignKey("Department", on_delete=models.CASCADE)

    # kis user ne create kiya
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # created time
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name
    
    
# ================= RECIPE MASTER =================
class Recipe(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)

    finished_product = models.ForeignKey("Product", on_delete=models.CASCADE)
    department = models.ForeignKey("Department", on_delete=models.CASCADE)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.finished_product}"


# ================= RECIPE ITEMS =================
class RecipeItem(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="items")
    yarn = models.ForeignKey("Yarn", on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey("Product", on_delete=models.CASCADE, null=True, blank=True)
    percentage = models.FloatField()

    class Meta:
        # ❌ duplicate yarn in same recipe block
        unique_together = ('recipe', 'yarn')

    def __str__(self):
        if self.yarn:
            return f"{self.yarn} ({self.percentage}%)"
        if self.product:
            return f"{self.product} ({self.percentage}%)"