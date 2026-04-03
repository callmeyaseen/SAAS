from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'mpr']


class PurchaseOrderItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'mpr_quantity', 'quantity', 'rate']


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=0,
    can_delete=False
)