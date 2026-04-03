from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from decimal import Decimal
from utilities.models import Vendor
from .models import  Yarn, MPR, MPRItem

# ================= MPR AUTO NUMBER =================
def generate_mpr_no():

    last = MPR.objects.order_by("-id").first()

    if last and last.mpr_no:

        try:
            number = int(last.mpr_no.split("-")[1]) + 1
        except:
            number = 1

    else:
        number = 1

    return f"MPR-{number:04d}"


# ================= MPR ENTRY =================
@login_required(login_url="user_login")
def mpr_entry(request):

    yarns = Yarn.objects.all()
    vendors = Vendor.objects.all()

    mpr = None
    items = []

    mpr_no = generate_mpr_no()

    # ================= FIND =================
    if request.method == "POST" and "find" in request.POST:

        search_no = request.POST.get("search_mpr_no")

        mpr = MPR.objects.filter(mpr_no=search_no).first()

        if not mpr:

            messages.error(request, "MPR Not Found")

        else:

            mpr_no = mpr.mpr_no
            items = mpr.items.all()


    # ================= SAVE =================
    elif request.method == "POST" and "save" in request.POST:

        mpr = MPR.objects.create(
            mpr_no=mpr_no,
            required_date=request.POST.get("required_date"),
            request_from=request.POST.get("request_from"),
            department=request.POST.get("department"),
            suggested_vendor_id=request.POST.get("vendor"),
            created_by=request.user
        )

        items = request.POST.getlist("item[]")
        quantities = request.POST.getlist("quantity[]")
        rates = request.POST.getlist("rate[]")

        for item_name, qty, rate in zip(items, quantities, rates):

            if item_name and qty:

                qty = Decimal(qty)
                rate = Decimal(rate) if rate else Decimal("0")

                yarn = Yarn.objects.filter(item_name=item_name).first()

                if yarn:

                    MPRItem.objects.create(
                        mpr=mpr,
                        item=yarn,
                        quantity=qty,
                        rate=rate,
                        amount=qty * rate
                    )

        messages.success(request, "MPR Created Successfully")

        return redirect("mpr_entry")


    # ================= UPDATE =================
    elif request.method == "POST" and "update" in request.POST:

        mpr_no = request.POST.get("mpr_no")

        mpr = MPR.objects.filter(mpr_no=mpr_no).first()

        if mpr:

            mpr.required_date = request.POST.get("required_date")
            mpr.request_from = request.POST.get("request_from")
            mpr.department = request.POST.get("department")

            mpr.save()

            # delete old items
            mpr.items.all().delete()

            items = request.POST.getlist("item[]")
            quantities = request.POST.getlist("quantity[]")
            rates = request.POST.getlist("rate[]")

            for item_name, qty, rate in zip(items, quantities, rates):

                if item_name and qty:

                    qty = Decimal(qty)
                    rate = Decimal(rate) if rate else Decimal("0")

                    yarn = Yarn.objects.filter(item_name=item_name).first()

                    if yarn:

                        MPRItem.objects.create(
                            mpr=mpr,
                            item=yarn,
                            quantity=qty,
                            rate=rate,
                            amount=qty * rate
                        )

            messages.success(request, "MPR Updated Successfully")

            return redirect("mpr_entry")

        else:
            messages.error(request, "MPR Not Found")


    return render(
        request,
        "inventory/mpr_entry.html",
        {
            "mpr": mpr,
            "mpr_no": mpr_no,
            "items": items,
            "yarns": yarns,
            "vendors": vendors, 
            "today": timezone.now().date()
        }
    )


# ================= MPR LIST =================
@login_required(login_url="user_login")
def mpr_list(request):

    mprs = MPR.objects.all().order_by("-created_at")

    return render(
        request,
        "inventory/mpr_list.html",
        {"mprs": mprs}
    )


# ================= MPR REPORT =================
@login_required(login_url="user_login")
def mpr_report(request, mpr_no):

    mpr = MPR.objects.filter(mpr_no=mpr_no).first()

    return render(
        request,
        "inventory/mpr_report.html",
        {"mpr": mpr}
    )
    
