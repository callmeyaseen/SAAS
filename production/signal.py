from django.db.models.signals import post_save
from django.dispatch import receiver

from production.models import WorkOrder, WorkOrderItem

# =========================================================
# AUTO CREATE WORK ORDER ITEMS
# =========================================================

@receiver(post_save, sender=WorkOrder)
def create_work_order_items(sender, instance, created, **kwargs):

    if created and instance.recipe:

        recipe_items = instance.recipe.items.all()

        for item in recipe_items:

            required_qty = (
                instance.order_qty * item.percentage
            ) / 100

            WorkOrderItem.objects.create(

                work_order=instance,

                yarn=item.yarn if item.yarn else None,

                product=item.product if item.product else None,

                unit_qty=item.percentage,

                required_qty=required_qty
            )