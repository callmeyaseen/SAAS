import re
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseForbidden
from .models import Department, Product, Rack, Recipe, RecipeItem, Vendor, Yarn ,Recipe, RecipeItem
from security.utils import get_permission
from django.contrib.auth.models import User
from datetime import date
from django.db import IntegrityError
from django.db.models import Q
from django.db import transaction
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
    departments = Department.objects.all()

    if request.method == "POST":

        rack_no = request.POST.get("rack_no")
        department = request.POST.get("department")
        location = request.POST.get("location")

        # 🔥 validation
        if not rack_no or not department:
            messages.error(request, "Rack No and Department required")
            return redirect("rack_entry")

        # 🔥 SAFE conversion
        if not str(department_id).isdigit():
            messages.error(request, "Invalid Department")
            return redirect("rack_entry")

        department_id = int(department_id)  # 🔥 FIX

        # 🔥 duplicate check
        if Rack.objects.filter(rack_no=rack_no, department_id=department_id).exists():
            messages.error(request, "This rack already exists in this department")
            return redirect("rack_entry")

        # ✅ save
        Rack.objects.create(
            rack_no=rack_no,
            department=department,
            location=location,
            created_by=request.user
        )

        messages.success(request, "Rack created successfully")
        return redirect("rack_entry")

    return render(request, "utilities/rack_entry.html", {
        "departments": departments
    })
def rack_delete(request, id):

    rack = get_object_or_404(Rack, id=id)

    rack.delete()

    messages.success(request, "Rack deleted successfully")

    return redirect("rack_list")
def rack_list(request):

    racks = Rack.objects.all().order_by("-id")

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

# ================= Department =================
@login_required(login_url="user_login")
def department_entry(request):

    # SAVE
    if request.method == "POST":

        name = request.POST.get("name")
        dept_type = request.POST.get("department_type")

        if name and dept_type:

            Department.objects.create(
                name=name,
                department_type=dept_type,
                created_by=request.user
            )

            messages.success(request, "Department Created Successfully")
            return redirect("department_entry")

        else:
            messages.error(request, "All fields are required")

    # LIST
    departments = Department.objects.all().order_by("-id")

    return render(request, "utilities/department_entry.html", {
        "departments": departments
    })



# ================= AUTO VOUCHER FUNCTION =================
def generate_voucher():
    # last product get karo (latest entry)
    last_product = Product.objects.order_by('-id').first()

    if last_product and last_product.voucher_no:
        # number extract karo (V-0001 → 1)
        match = re.search(r'\d+', last_product.voucher_no)

        if match:
            last_number = int(match.group())
            new_number = last_number + 1
        else:
            new_number = 1
    else:
        new_number = 1

    # formatted voucher
    return f"V-{new_number:04d}"


@login_required(login_url="user_login")
def product_entry(request):

    departments = Department.objects.all()
    product = None
    voucher_auto = generate_voucher()

    if request.method == "POST":

        action = request.POST.get("action")
        voucher_no = request.POST.get("voucher_no")
        product_name = request.POST.get("product_name")
        department_id = request.POST.get("department")

        # ================= SAVE =================
        if action == "save":

            if product_name and department_id:
                try:
                    with transaction.atomic():
                        # ✅ Duplicate check (case-insensitive)
                        if Product.objects.filter(product_name__iexact=product_name).exists():
                            messages.error(request, "Product already exists!")
                            return redirect("product_entry")

                        Product.objects.create(
                            voucher_no=voucher_auto,
                            product_name=product_name,
                            department_id=department_id,
                            created_by=request.user
                        )
                        messages.success(request, "Product Saved Successfully")
                        return redirect("product_entry")
                except IntegrityError:
                    messages.error(request, "Duplicate product not allowed!")
                    return redirect("product_entry")

            else:
                messages.error(request, "All fields are required")

        # ================= FIND =================
        elif action == "find":

            if voucher_no:
                try:
                    product = Product.objects.get(voucher_no=voucher_no)
                    messages.success(request, "Product Found")

                except Product.DoesNotExist:
                    messages.error(request, "No product found")

            elif product_name:
                product = Product.objects.filter(
                    product_name__icontains=product_name
                ).order_by('-id').first()

                if product:
                    messages.success(request, "Product Found")
                else:
                    messages.error(request, "No product found")

            else:
                messages.error(request, "Enter Voucher OR Product Name")

        # ================= UPDATE =================
        elif action == "update":

            if voucher_no:
                try:
                    with transaction.atomic():
                        product = Product.objects.get(voucher_no=voucher_no)

                        # ✅ Duplicate check (exclude self)
                        if Product.objects.filter(
                            product_name__iexact=product_name
                        ).exclude(id=product.id).exists():
                            messages.error(request, "Product name already exists!")
                            return redirect("product_entry")

                        product.product_name = product_name
                        product.department_id = department_id
                        product.save()

                        messages.success(request, "Product Updated Successfully")
                        return redirect("product_entry")
                except Product.DoesNotExist:
                    messages.error(request, "Product Not Found")

            else:
                messages.error(request, "Voucher required")

        # ================= DELETE =================
        elif action == "delete":

            if voucher_no:
                try:
                    product = Product.objects.get(voucher_no=voucher_no)
                    product.delete()

                    messages.success(request, "Product Deleted Successfully")
                    return redirect("product_entry")

                except Product.DoesNotExist:
                    messages.error(request, "Product Not Found")

            else:
                messages.error(request, "Voucher required")

    return render(request, "utilities/product_entry.html", {
        "departments": departments,
        "product": product,
        "today": date.today(),
        "voucher_auto": voucher_auto
    })
@login_required(login_url="user_login")
def product_list(request):

    # filters
    search = request.GET.get("search")  # search input
    department_id = request.GET.get("department")

    # base queryset
    products = Product.objects.select_related("department", "created_by").order_by("-id")

    # 🔍 SEARCH (voucher OR product name)
    if search:
        products = products.filter(
            Q(voucher_no__icontains=search) |
            Q(product_name__icontains=search)
        )

    # 🎯 DEPARTMENT FILTER
    if department_id:
        products = products.filter(department_id=department_id)

    # dropdown ke liye departments
    departments = Department.objects.all()

    return render(request, "utilities/product_list.html", {
        "products": products,
        "departments": departments,
        "search": search,
        "selected_department": department_id
    })
    
def product_view(request, voucher_no):

    product = get_object_or_404(Product, voucher_no=voucher_no)

    return render(request, "utilities/product_view.html", {
        "product": product
    })



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from datetime import date
from .models import Recipe, RecipeItem, Product, Yarn, Department


# ================= AUTO VOUCHER =================
def generate_recipe_voucher():
    last = Recipe.objects.order_by("-id").first()

    if last and last.voucher_no:
        try:
            num = int(last.voucher_no.split("-")[1]) + 1
        except:
            num = 1
    else:
        num = 1

    return f"RCP-{num:04d}"


# ================= MAIN VIEW =================
@login_required(login_url="user_login")
def recipe_entry(request):

    departments = Department.objects.all()
    products = Product.objects.all()
    yarns = Yarn.objects.all()

    voucher_auto = generate_recipe_voucher()
    recipe = None
    recipe_items = []

    if request.method == "POST":

        action = request.POST.get("action")
        voucher_no = request.POST.get("voucher_no")
        product_id = request.POST.get("finished_item")
        department_id = request.POST.get("department")

        items = request.POST.getlist("item_type[]")   # 🔥 NEW (product + yarn)
        percentages = request.POST.getlist("percentage[]")

        # ================= SAVE =================
        if action == "save":

            if not (product_id and department_id):
                messages.error(request, "All fields required")
                return redirect("recipe_entry")

            if Recipe.objects.filter(finished_product_id=product_id).exists():
                messages.error(request, "Recipe already exists for this product")
                return redirect("recipe_entry")

            # float comparison fix (rounding to avoid 99.99999 error)
            total = round(sum([float(p) for p in percentages if p]), 2)

            if total != 100.0:
                messages.error(request, "Total must be exactly 100%")
                return redirect("recipe_entry")

            try:
                with transaction.atomic():
                    recipe = Recipe.objects.create(
                        voucher_no=voucher_auto,
                        finished_product_id=product_id,
                        department_id=department_id,
                        created_by=request.user
                    )

                    used_items = set()
                    for item, p in zip(items, percentages):
                        if not item or not p: continue

                        if item in used_items:
                            raise ValueError("Duplicate item not allowed in recipe")
                        used_items.add(item)

                        if "product_" in item:
                            RecipeItem.objects.create(recipe=recipe, product_id=item.split("_")[1], percentage=p)
                        elif "yarn_" in item:
                            RecipeItem.objects.create(recipe=recipe, yarn_id=item.split("_")[1], percentage=p)

                messages.success(request, "Recipe Saved Successfully ✅")
                return redirect("recipe_entry")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
                return redirect("recipe_entry")

        # ================= FIND =================
        elif action == "find":

            if voucher_no:
                recipe = Recipe.objects.filter(voucher_no=voucher_no).first()

            elif product_id:
                recipe = Recipe.objects.filter(
                    finished_product_id=product_id
                ).first()

            if recipe:
                recipe_items = recipe.items.all()
                messages.success(request, "Recipe Found")
            else:
                messages.error(request, "Recipe not found")

        # ================= UPDATE =================
        elif action == "update":

            recipe = Recipe.objects.filter(voucher_no=voucher_no).first()

            if not recipe:
                messages.error(request, "Recipe not found")
                return redirect("recipe_entry")

            total = round(sum([float(p) for p in percentages if p]), 2)

            if total != 100.0:
                messages.error(request, "Total must be exactly 100%")
                return redirect("recipe_entry")

            try:
                with transaction.atomic():
                    # delete old items
                    recipe.items.all().delete()
                    used_items = set()

                    for item, p in zip(items, percentages):
                        if not item or not p: continue
                        if item in used_items:
                            raise ValueError("Duplicate item detected during update")
                        used_items.add(item)

                        if "product_" in item:
                            RecipeItem.objects.create(recipe=recipe, product_id=item.split("_")[1], percentage=p)
                        elif "yarn_" in item:
                            RecipeItem.objects.create(recipe=recipe, yarn_id=item.split("_")[1], percentage=p)

                    # Update header if needed
                    recipe.department_id = department_id
                    recipe.finished_product_id = product_id
                    recipe.save()

                messages.success(request, "Recipe Updated Successfully")
                return redirect("recipe_entry")
            except Exception as e:
                messages.error(request, f"Update Failed: {str(e)}")
                return redirect("recipe_entry")

        # ================= DELETE =================
        elif action == "delete":

            recipe = Recipe.objects.filter(voucher_no=voucher_no).first()

            if recipe:
                recipe.delete()
                messages.success(request, "Recipe Deleted Successfully")
            else:
                messages.error(request, "Recipe not found")

            return redirect("recipe_entry")

        # ================= VIEW =================
        elif action == "view":

            recipes = Recipe.objects.all().order_by("-id")

            return render(request, "utilities/recipe_report.html", {
                "recipes": recipes
            })

    return render(request, "utilities/recipe_entry.html", {
        "departments": departments,
        "products": products,
        "yarns": yarns,
        "voucher_auto": voucher_auto,
        "today": date.today(),
        "recipe": recipe,
        "recipe_items": recipe_items
    })