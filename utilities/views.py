from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .models import Rack, Vendor, Yarn
from security.utils import get_permission
from django.contrib.auth.models import User
@login_required(login_url='user_login')
def vendor_entry(request):

    vendor = None

    # 🔹 AUTO LOAD FROM LIST (GET)
    code = request.GET.get("code")
    if code:
        try:
            vendor = Vendor.objects.get(vendor_code=code)
        except Vendor.DoesNotExist:
            vendor = None

    # ---------------- SAVE ----------------
    if request.method == "POST" and "save" in request.POST:
        if not request.user.has_perm("utilities.add_vendor"):
            return HttpResponse("You are not allowed to create vendor.")

        Vendor.objects.create(
            vendor_name=request.POST.get("vendor_name"),
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
            address=request.POST.get("address"),
        )

        messages.success(request, "Vendor saved successfully!")
        return redirect("vendor_entry")

    # ---------------- FIND ----------------
    if request.method == "POST" and "find" in request.POST:
        if not request.user.has_perm("utilities.view_vendor"):
            return HttpResponse("You are not allowed to view vendor.")

        code = request.POST.get("search_code")

        try:
            vendor = Vendor.objects.get(vendor_code=code)
        except Vendor.DoesNotExist:
            messages.error(request, "Vendor not found!")

    # ---------------- UPDATE ----------------
    if request.method == "POST" and "update" in request.POST:
        if not request.user.has_perm("utilities.change_vendor"):
            return HttpResponse("You are not allowed to update vendor.")

        code = request.POST.get("vendor_code")

        try:
            vendor = Vendor.objects.get(vendor_code=code)

            vendor.vendor_name = request.POST.get("vendor_name")
            vendor.phone = request.POST.get("phone")
            vendor.email = request.POST.get("email")
            vendor.address = request.POST.get("address")
            vendor.save()

            messages.success(request, "Vendor updated successfully!")

        except Vendor.DoesNotExist:
            messages.error(request, "Vendor not found!")

        return redirect("vendor_entry")

    # ---------------- DELETE ----------------
    if request.method == "POST" and "delete" in request.POST:
        if not request.user.has_perm("utilities.delete_vendor"):
            return HttpResponse("You are not allowed to delete vendor.")

        code = request.POST.get("vendor_code")

        try:
            Vendor.objects.get(vendor_code=code).delete()
            messages.success(request, "Vendor deleted successfully!")
        except Vendor.DoesNotExist:
            messages.error(request, "Vendor not found!")

        return redirect("vendor_entry")

    return render(
        request,
        "utilities/vendor_entry.html",
        {
            "vendor": vendor
        }
    )


# =========================
# VENDOR LIST (FIXED)
# =========================
@login_required(login_url='user_login')
def vendor_list(request):

    if not request.user.has_perm("utilities.view_vendor"):
        return HttpResponse("You are not allowed to view vendors.")

    vendors = Vendor.objects.all().order_by("vendor_name")

    return render(
        request,
        "utilities/vendor_list.html",
        {
            "vendors": vendors
        }
    )    
# ================= Rack Entry View =================
def rack_entry(request):

    racks = Rack.objects.all().order_by("-id")

    if request.method == "POST":

        rack_no = request.POST.get("rack_no")
        location = request.POST.get("location")
        created_by = request.user

        if Rack.objects.filter(rack_no=rack_no).exists():
            messages.error(request, "Rack already exists")
        else:
            Rack.objects.create(
                rack_no=rack_no,
                location=location,
                created_by=created_by
            )
            messages.success(request, "Rack Created Successfully")

        return redirect("rack_entry")

    return render(
        request,
        "utilities/rack_entry.html",
        {"racks": racks}
    )
    
# ✅ RACK LIST (TABLE)
def rack_list(request):
    racks = Rack.objects.all()

    return render(request, "utilities/rack_list.html", {
        "racks": racks
    })
    

# ================= AUTO YARN CODE =================
def generate_yarn_code():

    last_yarn = Yarn.objects.order_by("-id").first()

    if last_yarn and last_yarn.yarn_code:

        try:
            last_number = int(last_yarn.yarn_code.split("-")[1])
            new_number = last_number + 1
        except:
            new_number = 1
    else:
        new_number = 1

    return f"YRN-{new_number:04d}"


# ================= YARN ENTRY =================
@login_required(login_url="user_login")
def yarn_entry(request):

    yarn = None
    new_code = generate_yarn_code()

    if request.method == "POST":

        # -------- FIND --------
        if "find" in request.POST:

            code = request.POST.get("yarn_code")
            name = request.POST.get("item_name")

            yarn = Yarn.objects.filter(
                yarn_code=code
            ).first() or Yarn.objects.filter(
                item_name__icontains=name
            ).first()

            if not yarn:
                messages.error(request, "Yarn not found")


        # -------- SAVE --------
        elif "save" in request.POST:

            code = generate_yarn_code()

            Yarn.objects.create(
                yarn_code=code,
                item_name=request.POST.get("item_name"),
                unit=request.POST.get("unit"),
                shade=request.POST.get("shade"),
                yarn_type=request.POST.get("yarn_type"),
                # vendor_id = request.POST.get("vendors"),
                created_by=request.user,
                updated_by=request.user,
            )

            messages.success(request, f"Yarn Saved Successfully (Code: {code})")

            return redirect("yarn_entry")


        # -------- UPDATE --------
        elif "update" in request.POST:

            code = request.POST.get("yarn_code")

            yarn = Yarn.objects.filter(yarn_code=code).first()

            if yarn:

                yarn.item_name = request.POST.get("item_name")
                yarn.unit = request.POST.get("unit")
                yarn.shade = request.POST.get("shade")
                yarn.yarn_type = request.POST.get("yarn_type")
                yarn.updated_by = request.user

                yarn.save()

                messages.success(request, "Yarn Updated Successfully")

                return redirect("yarn_entry")

            else:
                messages.error(request, "Yarn not found for update")


        # -------- DELETE --------
        elif "delete" in request.POST:

            code = request.POST.get("yarn_code")

            yarn = Yarn.objects.filter(yarn_code=code).first()

            if yarn:

                yarn.delete()

                messages.success(request, "Yarn Deleted Successfully")

                return redirect("yarn_entry")

            else:
                messages.error(request, "Yarn not found for delete")


        # -------- VIEW REPORT --------
        elif "view" in request.POST:

            yarn_list = Yarn.objects.all().order_by("-created_at")

            return render(
                request,
                "inventory/yarn_report.html",
                {"yarns": yarn_list}
            )


    return render(
        request,
        "utilities/yarn_entry.html",
        {
            "yarn": yarn,
            "new_code": new_code
        }
    )


# ================= YARN FILTER =================
@login_required(login_url="user_login")
def yarn_filter(request):

    users = User.objects.all()

    if request.method == "POST":

        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        created_by = request.POST.get("created_by")
        item_name = request.POST.get("item_name")

        yarns = Yarn.objects.all()

        if from_date and to_date:

            yarns = yarns.filter(
                created_at__date__range=[from_date, to_date]
            )

        elif from_date:

            yarns = yarns.filter(
                created_at__date=from_date
            )

        if created_by:
            yarns = yarns.filter(created_by_id=created_by)

        if item_name:
            yarns = yarns.filter(item_name__icontains=item_name)

        yarns = yarns.order_by("-created_at")

        return render(
            request,
            "utilities/yarn_filter_report.html",
            {"yarns": yarns}
        )

    return render(
        request,
        "utilities/yarn_filter.html",
        {"users": users}
    )
