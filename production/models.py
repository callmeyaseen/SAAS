
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from utilities.models import (Customer,Machine,Recipe,RecipeItem,Product, Yarn, Department)
from sale.models import SaleOrder

class ProductionPlan(models.Model):

    plan_no = models.CharField(max_length=50, unique=True)

    work_order = models.ForeignKey('WorkOrder', on_delete=models.CASCADE, null=True, blank=True)

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

class RollInspection(models.Model):
    roll = models.ForeignKey(ProductionRoll, on_delete=models.CASCADE, related_name='inspections')
    voucher_no = models.CharField(max_length=50, unique=True)
    inspected_at = models.DateTimeField(auto_now_add=True)
    four_point_faults = models.IntegerField(default=0)
    press_hole = models.IntegerField(default=0)
    rafu = models.IntegerField(default=0)
    needle_break = models.IntegerField(default=0)
    double_kunda = models.IntegerField(default=0)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.voucher_no} - {self.roll.roll_no}"

# ===================# WORK ORDER MASTER # ================================
class WorkOrder(models.Model):

    STATUS_CHOICES = (('Pending', 'Pending'),('In Progress', 'In Progress'),('Completed', 'Completed'),)
    work_order_no = models.CharField(max_length=10,unique=True,blank=True)
    work_order_date = models.DateField()
    sale_order = models.ForeignKey(SaleOrder,on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,blank=True)
    order_product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True,related_name='wo_order_product')
    produced_product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True,related_name='wo_produced_product')
    yarn = models.ForeignKey(Yarn,on_delete=models.SET_NULL,null=True,blank=True)
    recipe = models.ForeignKey(Recipe,on_delete=models.SET_NULL,null=True,blank=True)
    department = models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True)
    order_qty = models.FloatField(default=0)
    start_delivery_date = models.DateField(null=True,blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # =====================# AUTO GENERATE + AUTO FETCH # ===================================
    def save(self, *args, **kwargs):
        if not self.work_order_no:
            last_wo = WorkOrder.objects.order_by('-id').first()
            if last_wo:
                last_id = last_wo.id
                new_id = last_id + 1
            else:
                new_id = 1
            self.work_order_no = f"WO{new_id:04d}"
        # ================= SALE ORDER DATA FETCH =================
        if self.sale_order:
            self.customer = self.sale_order.customer
            self.order_qty = self.sale_order.order_qty
            self.start_delivery_date = self.sale_order.end_delivery_date

            # Logic to find the correct recipe based on the WorkOrder's Production Department
            main_product = self.sale_order.product
            if not main_product and self.sale_order.yarn:
                main_product = Product.objects.filter(product_name__iexact=self.sale_order.yarn.item_name).first()
            
            self.order_product = main_product
            target_dept = self.department
            
            # If department matches Sale Order product, use main recipe
            if main_product and target_dept and main_product.department == target_dept:
                self.produced_product = main_product
                self.recipe = Recipe.objects.filter(finished_product=main_product, department=target_dept).first()
            elif main_product and target_dept:
                # Recursive search for intermediate recipe (e.g. Spinning recipe for a Knitting order)
                def get_recipe_for_dept(current_recipe, dept_obj, visited=None):
                    if not current_recipe or not dept_obj: return None
                    if visited is None: visited = set()
                    if current_recipe.id in visited: return None
                    visited.add(current_recipe.id)
                    
                    for item in current_recipe.items.all():
                        comp_p = item.product
                        if not comp_p and item.yarn:
                            comp_p = Product.objects.filter(product_name__iexact=item.yarn.item_name.strip(), department=dept_obj).first()
                        
                        if comp_p and comp_p.department == dept_obj:
                            r = Recipe.objects.filter(finished_product=comp_p, department=dept_obj).first()
                            if r: return (comp_p, r)  # Ensure returning the product proxy
                        
                        # Recurse deeper
                        candidate = comp_p
                        if not candidate and item.yarn:
                            candidate = Product.objects.filter(product_name__iexact=item.yarn.item_name.strip()).first()
                        
                        if candidate:
                            sub_r = Recipe.objects.filter(finished_product=candidate).first()
                            result = get_recipe_for_dept(sub_r, dept_obj, visited)
                            if result: return result
                    return None

                main_r = Recipe.objects.filter(finished_product=main_product).first()
                res = get_recipe_for_dept(main_r, target_dept)
                if res:
                    self.produced_product, self.recipe = res
            if self.sale_order.yarn:
                self.yarn = self.sale_order.yarn
        super().save(*args, **kwargs)
    def __str__(self):
        return self.work_order_no
# =======================# WORK ORDER ITEMS# ===============================
class WorkOrderItem(models.Model):
    work_order = models.ForeignKey(WorkOrder,on_delete=models.CASCADE,related_name='items')
    yarn = models.ForeignKey(Yarn,on_delete=models.SET_NULL,null=True,blank=True)
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True)
    unit_qty = models.FloatField()
    required_qty = models.FloatField()
    def __str__(self):
        if self.yarn:
            return str(self.yarn)
        if self.product:
            return str(self.product)
        return "Item"
