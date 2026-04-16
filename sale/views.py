from django.shortcuts import render, redirect, get_object_or_404
from .models import SaleOrder
from utilities.models import Product, Yarn

def generate_sale_no():
    
    products = Product.objects.all()
    
    last = SaleOrder.objects.order_by('-id').first()
    if last:
        last_no = int(last.sale_order_no.split('-')[-1])
        return f"SO-{last_no + 1:04d}"
    return "SO-0001"

def sale_create(request):

    allowed_departments = [
        "Knitting Finishing",
        "Stitching",
        "Spinning",
        "Covering",
        "Glove",
        "Flatknit"
    ]

    products = Product.objects.filter(
        department__name__in=allowed_departments
    )
    yarns = Yarn.objects.all()

    if request.method == "POST":

        item_type = request.POST.get('item_type') # "product" or "yarn"
        item_id = request.POST.get('item')

        if not item_id:
            return render(request, 'sale/form.html', {
                'products': products,
                'yarns': yarns,
                'error': 'Please select product'
            })

        product = Product.objects.get(id=item_id)

        SaleOrder.objects.create(
            sale_order_no=generate_sale_no(),
            so_date=request.POST.get('so_date'),
            customer_po_no=request.POST.get('customer_po_no'),
            customer_po_date=request.POST.get('customer_po_date'),
            category=request.POST.get('category'),
            customer_name=request.POST.get('customer_name'),

            product=product,

            order_qty=request.POST.get('order_qty'),
            fabric_width_type=request.POST.get('fabric_width_type'),
            fabric_width=request.POST.get('fabric_width'),
            unit=request.POST.get('unit'),
            finishing_process=request.POST.get('finishing_process'),
            cut_level=request.POST.get('cut_level'),
            sample_status=request.POST.get('sample_status'),
            received_by=request.POST.get('received_by'),
            shipment_location=request.POST.get('shipment_location'),
            delivery_date=request.POST.get('delivery_date'),
            order_type=request.POST.get('order_type'),
            payment_term=request.POST.get('payment_term'),
            price_order=request.POST.get('price_order'),
            rate=request.POST.get('rate'),
            currency_type=request.POST.get('currency_type'),
            currency_rate=request.POST.get('currency_rate'),
            description=request.POST.get('description'),
        )

        return redirect('sale:sale_list')

    return render(request, 'sale/form.html', {'products': products, 'yarns': yarns})
# LIST
def sale_list(request):
    sales = SaleOrder.objects.all().order_by('-id')
    return render(request, 'sale/list.html', {'sales': sales})
# UPDATE
def sale_update(request, pk):
    sale = get_object_or_404(SaleOrder, pk=pk)

    if request.method == "POST":
        sale.sale_order_no = request.POST.get('sale_order_no')
        sale.so_date = request.POST.get('so_date')
        sale.customer_po_no = request.POST.get('customer_po_no')
        sale.customer_po_date = request.POST.get('customer_po_date')
        sale.category = request.POST.get('category')
        sale.customer_name = request.POST.get('customer_name')
        sale.item_code = request.POST.get('item_code')
        sale.item_name = request.POST.get('item_name')
        sale.order_qty = request.POST.get('order_qty')
        sale.fabric_width_type = request.POST.get('fabric_width_type')
        sale.fabric_width = request.POST.get('fabric_width')
        sale.unit = request.POST.get('unit')
        sale.finishing_process = request.POST.get('finishing_process')
        sale.cut_level = request.POST.get('cut_level')
        sale.sample_status = request.POST.get('sample_status')
        sale.received_by = request.POST.get('received_by')
        sale.shipment_location = request.POST.get('shipment_location')
        sale.delivery_date = request.POST.get('delivery_date')
        sale.order_type = request.POST.get('order_type')
        sale.payment_term = request.POST.get('payment_term')
        sale.price_order = request.POST.get('price_order')
        sale.rate = request.POST.get('rate')
        sale.currency_type = request.POST.get('currency_type')
        sale.currency_rate = request.POST.get('currency_rate')
        sale.description = request.POST.get('description')

        sale.save()
        return redirect('sale:sale_list')

    return render(request, 'sale/form.html', {'sale': sale})

# DELETE
def sale_delete(request, pk):
    sale = get_object_or_404(SaleOrder, pk=pk)
    sale.delete()
    return redirect('sale:sale_list')


# DETAIL (VIEW BUTTON)
def sale_detail(request, pk):
    sale = get_object_or_404(SaleOrder, pk=pk)
    return render(request, 'sale/detail.html', {'sale': sale})