from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse

from inventory.models import MPR
from utilities.models import Vendor , Rack
from .models import GRN, GRNItem, PurchaseOrder, PurchaseOrderItem, Stock


# ================= PO LIST =================
@login_required
def po_list(request):

    query = request.GET.get('q')

    pos = PurchaseOrder.objects.all().order_by('-id')

    if query:
        pos = pos.filter(po_no__icontains=query)

    for po in pos:
        po.total_amount = sum(item.amount for item in po.items.all())

    return render(request, 'purchasing/po_list.html', {'pos': pos})


# ================= CREATE PO =================
@login_required
def create_po(request):

    vendors = Vendor.objects.all()
    mpr_items = []
    selected_mpr = None
    auto_supplier = None

    if request.method == "POST":

        # ---------------- FIND ----------------
        if "find_mpr" in request.POST:

            mpr_no = request.POST.get("search_mpr")
            selected_mpr = MPR.objects.filter(mpr_no=mpr_no).first()

            if selected_mpr:
                mpr_items = selected_mpr.items.all()
                auto_supplier = selected_mpr.suggested_vendor
            else:
                messages.error(request, "MPR not found")

        # ---------------- SAVE ----------------
        else:

            mpr_id = request.POST.get("mpr_id")
            supplier_id = request.POST.get("supplier")

            if not supplier_id:
                messages.error(request, "Supplier is required")
                return redirect("create_po")

            if not mpr_id:
                messages.error(request, "MPR missing")
                return redirect("create_po")

            selected_mpr = MPR.objects.get(id=mpr_id)

            po = PurchaseOrder.objects.create(
                supplier_id=supplier_id,
                mpr=selected_mpr,
                prepared_by=request.user
            )

            for item in selected_mpr.items.all():

                qty = request.POST.get(f"qty_{item.id}")
                rate = request.POST.get(f"rate_{item.id}")

                if qty and rate:

                    qty = float(qty)

                    if qty > float(item.quantity):
                        messages.error(
                            request,
                            f"PO quantity cannot exceed MPR quantity for {item.item}"
                        )
                        return redirect("create_po")

                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        item=item.item,
                        mpr_quantity=item.quantity,
                        quantity=qty,
                        rate=rate
                    )

            messages.success(request, "Purchase Order Created Successfully")
            return redirect("po_list")

    # ✅ SINGLE RETURN (IMPORTANT)
    return render(request, "purchasing/create_po.html", {
        "vendors": vendors,
        "mpr_items": mpr_items,
        "selected_mpr": selected_mpr,
        "auto_supplier": auto_supplier
    })
# ================= PO DETAIL =================
@login_required
def po_detail(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)
    items = po.items.all()

    total_amount = sum(item.amount for item in items)

    return render(request, 'purchasing/po_detail.html', {
        'po': po,
        'items': items,
        'total_amount': total_amount
    })


# ================= UPDATE PO =================
@login_required
def update_po(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status == "Approved":
        messages.error(request, "Approved PO cannot be edited")
        return redirect("po_detail", pk=pk)

    if request.method == "POST":

        for item in po.items.all():

            qty = request.POST.get(f"qty_{item.id}")
            rate = request.POST.get(f"rate_{item.id}")

            if qty and rate:
                item.quantity = qty
                item.rate = rate
                item.save()

        messages.success(request, "PO Updated Successfully")
        return redirect("po_detail", pk=pk)

    return render(request, "purchasing/update_po.html", {
        "po": po,
        "items": po.items.all()
    })


# ================= DELETE PO =================
@login_required
def delete_po(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status == "Approved":
        messages.error(request, "Approved PO cannot be deleted")
        return redirect("po_detail", pk=pk)

    po.delete()

    messages.success(request, "PO Deleted Successfully")

    return redirect("po_list")


# ================= PO APPROVAL LIST =================
@login_required
@permission_required('purchasing.can_approve_po', raise_exception=True)
def po_approval_list(request):

    pending_pos = PurchaseOrder.objects.filter(status="Pending").order_by('-id')

    return render(request, "purchasing/po_approval_list.html", {
        "pending_pos": pending_pos
    })


# ================= APPROVE PO =================
@login_required
@permission_required('purchasing.can_approve_po', raise_exception=True)
def approve_po(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status == "Pending":

        po.status = "Approved"
        po.approved_by = request.user
        po.approved_date = timezone.now()
        po.save()

        messages.success(request, "Purchase Order Approved")

    return redirect("po_approval_list")


# ================= REJECT PO =================
@login_required
@permission_required('purchasing.can_approve_po', raise_exception=True)
@require_POST
def reject_po(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status == "Pending":

        po.status = "Rejected"
        po.rejected_by = request.user
        po.rejected_date = timezone.now()
        po.reject_reason = request.POST.get("reject_reason")

        po.save()

        messages.error(request, "Purchase Order Rejected")

    return redirect("po_approval_list")


# ================= REOPEN PO =================
@login_required
@permission_required('purchasing.can_approve_po', raise_exception=True)
def reopen_po(request, pk):

    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status == "Rejected":

        po.status = "Pending"
        po.rejected_by = None
        po.rejected_date = None
        po.reject_reason = None
        po.save()

        messages.success(request, "PO Reopened")

    return redirect("po_detail", pk=pk)


# ================= GRN NUMBER GENERATOR =================
def generate_grn_no():

    last = GRN.objects.order_by('-id').first()

    if last:
        last_no = int(last.grn_no.split('-')[1])
        number = last_no + 1
    else:
        number = 1

    return f"GRN-{number:04d}"


# ================= CREATE GRN =================
@login_required
def create_grn(request):

    pos = PurchaseOrder.objects.filter(status="Approved")
    racks = Rack.objects.all()   # 🔥 NEW
    new_grn_no = generate_grn_no()

    if request.method == "POST":

        po_id = request.POST.get("po")
        po = PurchaseOrder.objects.get(id=po_id)

        grn = GRN.objects.create(
            grn_no=new_grn_no,
            po=po,
            supplier=po.supplier,
            received_date=request.POST.get("received_date"),
            vehicle_no=request.POST.get("vehicle_no"),   # 🔥 NEW
            driver_name=request.POST.get("driver_name"), # 🔥 NEW
            received_by=request.user
        )

        items = request.POST.getlist("item[]")
        po_qty = request.POST.getlist("po_qty[]")
        rec_qty = request.POST.getlist("received_qty[]")
        rates = request.POST.getlist("rate[]")   # 🔥 NEW
        racks_selected = request.POST.getlist("rack[]")  # 🔥 NEW

        for item, pqty, rqty, rate, rack_id in zip(items, po_qty, rec_qty, rates, racks_selected):

            po_item = PurchaseOrderItem.objects.get(id=item)

            GRNItem.objects.create(
                grn=grn,
                item=po_item.item,
                po_qty=pqty,
                received_qty=rqty,
                rate=rate,
                rack_id=rack_id   # 🔥 FK shortcut
            )

            # 🔥 STOCK UPDATE
            stock, created = Stock.objects.get_or_create(
                item=po_item.item,
                rack_id=rack_id   # 🔥 yahi game changer hai
                )
            stock.quantity += float(rqty)
            stock.save()

        messages.success(request, "GRN Created Successfully")
        return redirect("grn_list")

    return render(request, "purchasing/create_grn.html", {
        "pos": pos,
        "racks": racks,   # 🔥 SEND
        "grn_no": new_grn_no
    })
# ================= GET PO ITEMS =================
@login_required
def get_po_items(request, po_id):

    items = PurchaseOrderItem.objects.filter(purchase_order_id=po_id)

    data = []

    for item in items:
        data.append({
            "id": item.id,
            "yarn": str(item.item),
            "qty": item.quantity
        })

    return JsonResponse(data, safe=False)

@login_required
def grn_detail(request, pk):
    grn = GRN.objects.select_related("po", "supplier").get(id=pk)
    items = GRNItem.objects.filter(grn=grn)

    return render(request, "purchasing/grn_detail.html", {
        "grn": grn,
        "items": items
    })
@login_required
def grn_delete(request, pk):
    grn = GRN.objects.get(id=pk)

    if request.method == "POST":
        grn.delete()
        messages.success(request, "GRN Deleted Successfully")
        return redirect("grn_list")

    return redirect("grn_list")
# ================= GRN LIST =================
@login_required
def grn_list(request):

    grns = GRN.objects.select_related("po", "supplier").order_by("-id")

    return render(request, "purchasing/grn_list.html", {"grns": grns})


# ================= STOCK LIST =================
@login_required
def stock_list(request):

    stocks = Stock.objects.all()

    return render(request, "purchasing/stock_list.html", {"stocks": stocks})