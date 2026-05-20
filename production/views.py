import re

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import ProductionPlan, ProductionRoll, QualityEntry, WorkOrder
from sale.models import SaleOrder
from utilities.models import Machine, Product, Department, Recipe
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.db import transaction
from django.contrib import messages

def generate_plan_no():
    last = ProductionPlan.objects.order_by('-id').first()
    if last:
        last_no = int(last.plan_no.split('-')[-1])
        return f"PLAN-{last_no + 1:04d}"
    return "PLAN-0001"

def get_so_details(request, pk):
    so = get_object_or_404(SaleOrder, pk=pk)
    target_dept_id = request.GET.get('dept_id')

    # Determine the starting product/recipe from Sale Order
    main_product = so.product
    if not main_product and so.yarn:
        # If SO is for Yarn, find the Product proxy to get its recipe
        main_product = Product.objects.filter(product_name__iexact=so.yarn.item_name).first()

    main_recipe = Recipe.objects.filter(finished_product=main_product).first()

    # Initialize target as the main item
    target_product = main_product
    display_recipe = main_recipe

    if target_dept_id:
        # Recursive function to find the recipe belonging to the target department
        def find_recipe_recursive(current_recipe, dept_id, visited=None):
            if not current_recipe: return None
            if visited is None: visited = set()
            if current_recipe.id in visited: return None
            visited.add(current_recipe.id)

            # 1. Check items in current recipe for a direct match in target department
            for item in current_recipe.items.all():
                comp_p = None
                if item.product:
                    comp_p = item.product
                elif item.yarn:
                    # Find Product proxy for this yarn in the target department
                    comp_p = Product.objects.filter(product_name__iexact=item.yarn.item_name.strip(), department_id=dept_id).first()
                    if not comp_p: # Fallback: search any product with this name to check its recipes later
                        comp_p = Product.objects.filter(product_name__iexact=item.yarn.item_name.strip()).first()

                if comp_p:
                    # Check if this component has a recipe in the target department
                    target_r = Recipe.objects.filter(finished_product=comp_p, department_id=dept_id).first()
                    if target_r:
                        return (comp_p, target_r)
                    
                    # If product belongs to dept but has no specific dept-recipe, check its main recipe
                    if str(comp_p.department_id) == str(dept_id):
                        target_r = Recipe.objects.filter(finished_product=comp_p).first()
                        if target_r: return (comp_p, target_r)

            # 2. If no direct match, recurse into sub-recipes of all components
            for item in current_recipe.items.all():
                sub_p = item.product
                if not sub_p and item.yarn:
                    sub_p = Product.objects.filter(product_name__iexact=item.yarn.item_name.strip()).first()
                
                if sub_p:
                    sub_r = Recipe.objects.filter(finished_product=sub_p).first()
                    result = find_recipe_recursive(sub_r, dept_id, visited)
                    if result: return result
            return None

        # Start search: prioritize main product recipe in target dept, then go recursive
        dept_recipe = Recipe.objects.filter(finished_product=main_product, department_id=target_dept_id).first()
        if dept_recipe:
            display_recipe = dept_recipe
        else:
            search_result = find_recipe_recursive(main_recipe, target_dept_id)
            if search_result:
                target_product, display_recipe = search_result
            elif main_product and str(main_product.department_id) != str(target_dept_id):
                display_recipe = None

    # Calculate total planned qty so far for this order
    already_planned = ProductionPlan.objects.filter(work_order__sale_order=so).aggregate(total_planned=Sum('planned_qty'))['total_planned'] or 0
    balance = so.order_qty - already_planned
    
    recipe_items_data = []
    if display_recipe:
        for item in display_recipe.items.all():
            item_name = ""
            if item.product:
                item_name = item.product.product_name
            elif item.yarn:
                item_name = item.yarn.item_name
            
            recipe_items_data.append({
                'item_name': item_name,
                'percentage': item.percentage,
            })

    # Resolve original department info
    if so.product and so.product.department:
        product_department_name = so.product.department.name
        product_department_id = so.product.department.id
    elif so.yarn:
        yp = Product.objects.filter(product_name__iexact=so.yarn.item_name).first()
        product_department_name = yp.department.name if yp and yp.department else "N/A"
        product_department_id = yp.department.id if yp and yp.department else None
    else:
        product_department_name = "N/A"
        product_department_id = None

    return JsonResponse({
        'order_qty': so.order_qty,
        'balance_qty': max(0, balance),
        'customer': so.customer.customer_name if so.customer else "N/A",
        'delivery_date': so.end_delivery_date.strftime('%Y-%m-%d') if so.end_delivery_date else "",
        'product_name': so.product.product_name if so.product else "N/A",
        'recipe_name': display_recipe.voucher_no if display_recipe else "No Recipe Found",
        'order_recipe_name': main_recipe.voucher_no if main_recipe else "No Recipe Found",
        'produced_item_name': target_product.product_name if target_product else "N/A",
        'produced_recipe_name': display_recipe.voucher_no if display_recipe else "No Recipe Found",
        'product_department_name': product_department_name,
        'product_department_id': product_department_id,
        'width_type': so.fabric_width_type,
        'width': so.fabric_width,
        'finishing': so.finishing_process,
        'status': so.status,
        'running_on': ProductionPlan.objects.filter(work_order__sale_order=so, status="Open").count(),
        'recipe_items': recipe_items_data,
    })

def get_wo_details(request, pk):
    """AJAX view to get details of a specific Work Order for planning."""
    wo = get_object_or_404(WorkOrder, pk=pk)
    so = wo.sale_order
    
    # Calculate balance based on this specific Work Order
    already_planned = ProductionPlan.objects.filter(work_order=wo).aggregate(total=Sum('planned_qty'))['total'] or 0
    balance = wo.order_qty - already_planned
    
    machine_queryset = Machine.objects.filter(is_active=True, department=wo.department)
    if not machine_queryset.exists():
        machine_queryset = Machine.objects.filter(is_active=True)
    machine_options = [
        {'id': m.id, 'label': f"{m.machine_name} ({m.machine_code})"}
        for m in machine_queryset
    ]

    return JsonResponse({
        'order_no': wo.work_order_no,
        'sale_order_no': so.sale_order_no,
        'customer': wo.customer.customer_name if wo.customer else "N/A",
        'product_name': wo.produced_product.product_name if wo.produced_product else "N/A",
        'department': wo.department.name if wo.department else "N/A",
        'order_qty': wo.order_qty,
        'balance_qty': max(0, balance),
        'delivery_date': wo.start_delivery_date.strftime('%Y-%m-%d') if wo.start_delivery_date else "",
        'recipe_name': wo.recipe.voucher_no if wo.recipe else "No Recipe",
        'status': wo.status,
        'width_type': so.fabric_width_type,
        'width': so.fabric_width,
        'finishing': so.finishing_process,
        'running_on': ProductionPlan.objects.filter(work_order=wo, status="Open").count(),
        'machine_options': machine_options,
    })

def get_machine_load(request):
    """AJAX view to check what is currently planned on a specific machine."""
    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({'plans': []})
    
    # Find machine by code or name
    machine = Machine.objects.filter(Q(machine_code__icontains=code) | Q(machine_name__icontains=code)).first()
    if not machine:
        return JsonResponse({'error': 'Machine not found'}, status=404)
        
    # Get all open plans for this machine and annotate with total scanned weight
    plans = ProductionPlan.objects.filter(machine=machine, status="Open").select_related('work_order', 'work_order__produced_product').annotate(
        total_scanned=Sum('rolls__weight')
    )
    
    load_data = []
    for p in plans:
        scanned = p.total_scanned or 0
        load_data.append({
            'plan_no': p.plan_no,
            'order_no': p.work_order.work_order_no,
            'article_name': p.work_order.produced_product.product_name if p.work_order.produced_product else "N/A",
            'planned_qty': p.planned_qty,
            'scanned_qty': scanned,
            'remaining_qty': round(max(0, p.planned_qty - scanned), 2),
            'start_date': p.start_date.strftime('%d-%b-%Y'),
            'end_date': p.end_date.strftime('%d-%b-%Y')
        })
    
    return JsonResponse({
        'machine_name': f"{machine.machine_name} ({machine.machine_code})",
        'plans': load_data
    })

def scan_roll(request):
    if request.method == "POST":
        plan_no = request.POST.get('plan_no')
        roll_no = request.POST.get('roll_no')
        weight = request.POST.get('weight')
        
        plan = ProductionPlan.objects.filter(plan_no=plan_no).first()
        if not plan:
            return JsonResponse({'error': 'Plan not found'}, status=404)
        
        try:
            ProductionRoll.objects.create(plan=plan, roll_no=roll_no, weight=float(weight))
            
            # 🔍 Fix: Use correct aggregate alias 'total_weight'
            scanned_data = ProductionRoll.objects.filter(plan=plan).aggregate(total_weight=Sum('weight'))
            total_scanned = scanned_data['total_weight'] or 0
            remaining_qty = round(max(0, plan.planned_qty - total_scanned), 2)

            return JsonResponse({'message': 'Roll scanned successfully', 'balance': remaining_qty})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

def roll_edit(request, pk):
    """Edits an existing ProductionRoll's number or weight."""
    if request.method == "POST":
        roll = get_object_or_404(ProductionRoll, pk=pk)
        new_no = request.POST.get('roll_no')
        new_weight = request.POST.get('weight')

        try:
            roll.roll_no = new_no
            roll.weight = float(new_weight)
            roll.save()

            scanned_data = ProductionRoll.objects.filter(plan=roll.plan).aggregate(total_weight=Sum('weight'))
            remaining_qty = round(max(0, roll.plan.planned_qty - (scanned_data['total_weight'] or 0)), 2)
            return JsonResponse({'message': 'Roll updated successfully', 'balance': remaining_qty})
        except Exception as e:
            return JsonResponse({'error': "Roll Number already exists or invalid data"}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

def roll_delete(request, pk):
    """Deletes a specific ProductionRoll entry."""
    roll = get_object_or_404(ProductionRoll, pk=pk)
    plan = roll.plan
    roll.delete()

    # Recalculate balance for the plan
    total_scanned = ProductionRoll.objects.filter(plan=plan).aggregate(total_weight=Sum('weight'))['total_weight'] or 0
    remaining_qty = round(max(0, plan.planned_qty - total_scanned), 2)
    return JsonResponse({'message': 'Roll deleted successfully', 'balance': remaining_qty})

def get_machine_plans(request, code):
    """Returns a list of open plans for a machine or specific plan no."""
    if not code or code == 'PLACEHOLDER':
        return JsonResponse({'plans': []})
        
    plans = ProductionPlan.objects.filter(
        (Q(machine__machine_code__iexact=code) | 
         Q(machine__machine_name__icontains=code) | 
         Q(plan_no__iexact=code)) & 
        Q(status="Open")
    ).select_related('work_order', 'work_order__produced_product', 'machine')

    data = [{
        'plan_no': p.plan_no,
        'machine': f"{p.machine.machine_name} ({p.machine.machine_code})" if p.machine else "N/A",
        'article': p.work_order.produced_product.product_name if p.work_order.produced_product else "N/A",
        'planned_qty': p.planned_qty,
    } for p in plans]

    return JsonResponse({'plans': data})


def generate_quality_entry_no():
    last_entry = QualityEntry.objects.order_by('-id').first()
    if last_entry and last_entry.entry_no:
        match = re.search(r'(\d+)$', last_entry.entry_no)
        if match:
            next_num = int(match.group(1)) + 1
        else:
            next_num = 1
    else:
        next_num = 1
    return f"QE-{next_num:04d}"


def quality_entry_form(request):
    selected_roll = None
    quality_entry = None
    default_entry_no = generate_quality_entry_no()
    roll_id = request.GET.get('roll_id')
    roll_no = request.GET.get('roll_no', '').strip()
    plan_no = request.GET.get('plan_no', '').strip()
    entry_search = request.GET.get('entry', '').strip()
    
    # Get rolls based on plan number if provided
    rolls = []
    if plan_no:
        plan = ProductionPlan.objects.filter(plan_no__iexact=plan_no).first()
        if plan:
            rolls = ProductionRoll.objects.filter(plan=plan).select_related('plan__work_order')

    if request.method == "POST":
        form_roll_id = request.POST.get('roll_id')
        entry_no = request.POST.get('entry_no', '').strip()

        if not form_roll_id:
            messages.error(request, "Please select a roll before saving quality entry.")
            return redirect('production:quality_entry_form')

        selected_roll = get_object_or_404(ProductionRoll, pk=form_roll_id)
        quality_entry = QualityEntry.objects.filter(roll=selected_roll).first()
        
        if not entry_no:
            entry_no = quality_entry.entry_no if quality_entry else generate_quality_entry_no()

        duplicate_entry = QualityEntry.objects.filter(entry_no__iexact=entry_no).exclude(roll=selected_roll).first()
        if duplicate_entry:
            messages.error(request, f"Entry {entry_no} is already assigned to another quality entry.")
        else:
            if quality_entry:
                quality_entry.entry_no = entry_no
            else:
                quality_entry = QualityEntry(roll=selected_roll, entry_no=entry_no)

            quality_entry.weight = float(request.POST.get('weight') or 0)
            quality_entry.fault_type = request.POST.get('fault_type', '').strip() or None
            quality_entry.press_hole = int(request.POST.get('press_hole') or 0)
            quality_entry.double_kunda = int(request.POST.get('double_kunda') or 0)
            quality_entry.needle_break = int(request.POST.get('needle_break') or 0)
            quality_entry.remarks = request.POST.get('remarks', '').strip()
            quality_entry.status = request.POST.get('status', 'Pass')
            quality_entry.save()

            messages.success(request, f"Quality entry saved with entry no {quality_entry.entry_no}.")
            return redirect(f"{reverse('production:quality_entry_form')}?entry={quality_entry.entry_no}")

    if entry_search:
        quality_entry = QualityEntry.objects.filter(entry_no__iexact=entry_search).select_related('roll__plan__work_order').first()
        if quality_entry:
            selected_roll = quality_entry.roll
        else:
            messages.warning(request, f"No quality entry found for entry no {entry_search}.")

    if roll_id and not selected_roll:
        selected_roll = ProductionRoll.objects.filter(pk=roll_id).select_related('plan__work_order').first()
        if selected_roll:
            quality_entry = QualityEntry.objects.filter(roll=selected_roll).first()

    if roll_no and not selected_roll:
        selected_roll = ProductionRoll.objects.filter(roll_no__iexact=roll_no).select_related('plan__work_order').first()
        if selected_roll:
            quality_entry = QualityEntry.objects.filter(roll=selected_roll).first()

    return render(request, 'production/quality_entry_form.html', {
        'selected_roll': selected_roll,
        'quality_entry': quality_entry,
        'default_entry_no': default_entry_no,
        'rolls': rolls,
        'plan_no': plan_no,
        'request': request,
    })


def quality_entry_delete(request, pk):
    quality_entry = get_object_or_404(QualityEntry, pk=pk)
    entry_no = quality_entry.entry_no
    quality_entry.delete()
    messages.success(request, f"Quality entry {entry_no} deleted successfully.")
    return redirect('production:quality_entry_form')


def get_rolls_by_plan(request, plan_no):
    """Fetch all rolls for a given plan number."""
    if not plan_no or plan_no == 'PLACEHOLDER':
        return JsonResponse({'rolls': []})
    
    plan = ProductionPlan.objects.filter(plan_no__iexact=plan_no).first()
    if not plan:
        return JsonResponse({'rolls': []})
    
    rolls = ProductionRoll.objects.filter(plan=plan).select_related('plan__work_order')
    data = [{
        'id': roll.id,
        'roll_no': roll.roll_no,
        'weight': roll.weight,
    } for roll in rolls]
    
    return JsonResponse({'rolls': data})


def plan_scan(request):
    """Dedicated page for scanning production rolls."""
    return render(request, 'production/plan_scan.html')

def get_next_roll(request, plan_no):
    """Helper to fetch plan details and generate next roll number automatically."""
    if not plan_no or plan_no == 'PLACEHOLDER':
        return JsonResponse({'error': 'Input required'}, status=400)

    # 🔍 Smart Search: Pehle Plan No se dhoondo, phir Machine Code se (sirf Open plans)
    plan = ProductionPlan.objects.filter(
        Q(plan_no__iexact=plan_no) | 
        (Q(machine__machine_code__iexact=plan_no) & Q(status="Open")) |
        (Q(machine__machine_name__icontains=plan_no) & Q(status="Open"))
    ).select_related('work_order', 'work_order__produced_product', 'machine').order_by('status', '-id').first()

    if not plan:
        return JsonResponse({'error': 'No active plan found for this input'}, status=404)

    # 🔍 Fix: Use correct aggregate alias 'total_weight'
    scanned_data = ProductionRoll.objects.filter(plan=plan).aggregate(total_weight=Sum('weight'))
    scanned = scanned_data['total_weight'] or 0
    
    # Generate Roll No based on REAL Plan No
    last_roll = ProductionRoll.objects.filter(plan=plan).order_by('-id').first()
    if last_roll:
        try:
            # Extract the last sequence after '-R'
            # Handle cases where hyphen might be missing or format different
            last_seq = int(last_roll.roll_no.split('-R')[-1]) 
            new_seq = last_seq + 1
        except:
            new_seq = 1
    else:
        new_seq = 1
    
    next_roll_no = f"{plan.plan_no}-R{new_seq:02d}"
    
    # Get existing rolls for this plan to display on frontend
    existing_rolls = ProductionRoll.objects.filter(plan=plan).order_by('created_at')
    rolls_data = [{
        'id': r.id,
        'roll_no': r.roll_no,
        'weight': r.weight,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
    } for r in existing_rolls]

    return JsonResponse({
        'plan_no': plan.plan_no,  # Send actual plan_no back to frontend
        'machine': f"{plan.machine.machine_name} ({plan.machine.machine_code})" if plan.machine else "N/A",
        'article': plan.work_order.produced_product.product_name if plan.work_order.produced_product else (plan.work_order.yarn.item_name if plan.work_order.yarn else "N/A"),
        'planned_qty': plan.planned_qty,
        'balance': round(max(0, plan.planned_qty - scanned), 2),
        'next_roll_no': next_roll_no,
        'rolls': rolls_data, # Send list of existing rolls
    })

def plan_create(request):
    departments = Department.objects.all()
    machines = Machine.objects.filter(is_active=True).select_related('department')
    next_plan_no = generate_plan_no()

    if request.method == "POST":
        department_id = request.POST.get('department')
        work_order_id = request.POST.get('work_order')
        machine_ids = request.POST.getlist('machine[]')
        planned_qtys = request.POST.getlist('planned_qty[]')
        start_dates = request.POST.getlist('start_date[]')
        end_dates = request.POST.getlist('end_date[]')
        m_statuses = request.POST.getlist('status[]')
        wo_status = request.POST.get('wo_status')

        # Get base plan number to avoid duplicates in loop
        current_plan_no = generate_plan_no()

        has_error = False
        if not department_id:
            messages.error(request, "Please select a department first.")
            has_error = True
        if not work_order_id:
            messages.error(request, "Please select a work order.")
            has_error = True
        if work_order_id and ProductionPlan.objects.filter(work_order_id=work_order_id).exists():
            messages.error(request, "Duplicate Error: This Work Order is already planned. Please select a different Work Order.")
            has_error = True
        for m_id in machine_ids:
            if m_id and ProductionPlan.objects.filter(work_order_id=work_order_id, machine_id=m_id).exists():
                m_obj = Machine.objects.filter(id=m_id).first()
                messages.error(request, f"Duplicate Error: Machine {m_obj.machine_name if m_obj else m_id} is already planned for this Work Order!")
                has_error = True

        if has_error:
            return render(request, 'production/plan_create.html', {
                'departments': departments,
                'machines': machines,
                'next_plan_no': next_plan_no,
            })

        with transaction.atomic():
            # Update Work Order Status
            wo_obj = WorkOrder.objects.get(id=work_order_id)
            wo_obj.status = wo_status
            wo_obj.save()

            # Counter for plan sequence increment within the loop
            plan_prefix = current_plan_no.split('-')[0]
            plan_start_num = int(current_plan_no.split('-')[-1])

            for m_id, qty, s_date, e_date, m_stat in zip(machine_ids, planned_qtys, start_dates, end_dates, m_statuses):
                if m_id and qty:
                    p_no = f"{plan_prefix}-{plan_start_num:04d}"
                    ProductionPlan.objects.create(
                        plan_no=p_no,
                        work_order_id=work_order_id,
                        machine_id=m_id,
                        planned_qty=qty,
                        start_date=s_date,
                        end_date=e_date,
                        status=m_stat,
                        remarks=request.POST.get('remarks'),
                    )
                    plan_start_num += 1

            messages.success(request, "Production Plan(s) Created Successfully.")
            return redirect('production:plan_list')

    return render(request, 'production/plan_create.html', {
        'departments': departments,
        'machines': machines,
        'next_plan_no': next_plan_no
    })


def get_work_orders_by_department(request, dept_id):
    work_orders = WorkOrder.objects.filter(
        department_id=dept_id,
        status__in=["Pending", "In Progress"]
    ).exclude(productionplan__isnull=False).select_related('sale_order', 'produced_product')

    results = [
        {
            'id': wo.id,
            'label': f"{wo.work_order_no}"
        }
        for wo in work_orders
    ]
    return JsonResponse({'work_orders': results})


def plan_edit(request, pk):
    plan = get_object_or_404(ProductionPlan, pk=pk)
    work_orders = WorkOrder.objects.all()
    machines = Machine.objects.filter(is_active=True)

    if request.method == "POST":
        # Update Plan Fields
        plan.machine_id = request.POST.get('machine')
        plan.planned_qty = request.POST.get('planned_qty')
        plan.start_date = request.POST.get('start_date')
        plan.end_date = request.POST.get('end_date')
        plan.status = request.POST.get('status')
        plan.remarks = request.POST.get('remarks')
        
        # Work Order Status update (optional)
        wo_status = request.POST.get('wo_status')

        with transaction.atomic():
            plan.save()
            if wo_status:
                plan.work_order.status = wo_status
                plan.work_order.save()

        messages.success(request, f"Production Plan {plan.plan_no} updated successfully.")
        return redirect('production:plan_list')

    return render(request, 'production/plan_edit.html', {
        'plan': plan,
        'work_orders': work_orders,
        'machines': machines
    })


def plan_list(request):
    search_query = request.GET.get('search', '')
    plans = ProductionPlan.objects.select_related('work_order', 'work_order__sale_order', 'work_order__customer', 'machine').all().order_by('-id')

    if search_query:
        plans = plans.filter(
            Q(plan_no__icontains=search_query) |
            Q(work_order__sale_order__sale_order_no__icontains=search_query) |
            Q(work_order__customer__customer_name__icontains=search_query)
        )

    return render(request, 'production/plan_list.html', {
        'plans': plans,
        'search_query': search_query
    })


def plan_detail(request, pk):
    plan = get_object_or_404(ProductionPlan, pk=pk)
    return render(request, 'production/plan_detail.html', {'plan': plan})


def plan_delete(request, pk):
    plan = get_object_or_404(ProductionPlan, pk=pk)
    plan.delete()
    return redirect('production:plan_list')

# ================ Work Orders ==================
def create_wo(request):
    search_wo = None
    wo_no = request.GET.get('wo_no', '').strip()
    if wo_no:
        search_wo = WorkOrder.objects.filter(work_order_no__iexact=wo_no).first()
        if not search_wo:
            messages.warning(request, f"No Work Order found for {wo_no}")

    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == "delete":
            wo_id = request.POST.get('wo_id')
            if wo_id:
                obj = get_object_or_404(WorkOrder, pk=wo_id)
                obj.delete()
                messages.success(request, "Work Order deleted successfully!")
                return redirect('production:create_wo')
            messages.error(request, "Please find a Work Order first to delete.")

        sale_order_id = request.POST.get('sale_order_id')
        wo_date = request.POST.get('work_order_date')
        requested_department_id = request.POST.get('requested_department_id')
        department_id = request.POST.get('department_id')
        status = request.POST.get('status', 'Pending')

        if not sale_order_id or not wo_date or not department_id:
            messages.error(request, "Sale Order, Date, and Production Department are required.")
        else:
            # Check if work order already exists for this sale order and production department
            existing_wo = WorkOrder.objects.filter(
                sale_order_id=sale_order_id,
                department_id=department_id
            ).first()
            
            if existing_wo:
                messages.error(request, f"Work Order is already generated against this Sale Order for the selected Production Department. Existing WO: {existing_wo.work_order_no}")
            else:
                try:
                    WorkOrder.objects.create(
                        sale_order_id=sale_order_id,
                        department_id=department_id,
                        work_order_date=wo_date,
                        status=status,
                        created_by=request.user
                    )
                    messages.success(request, "Work Order Created Successfully! Items will be generated via Signal.")
                    return redirect('production:create_wo')
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")

    sales = SaleOrder.objects.filter(status="Open")
    departments = Department.objects.all()
    return render(request, 'production/create_wo.html', {
        'sales': sales,
        'departments': departments,
        'search_wo': search_wo,
    })


def wo_list(request):
    q = request.GET.get('q', '').strip()
    work_orders = WorkOrder.objects.all().select_related('sale_order', 'customer', 'department', 'recipe')
    if q:
        work_orders = work_orders.filter(
            Q(work_order_no__icontains=q) |
            Q(sale_order__sale_order_no__icontains=q) |
            Q(customer__customer_name__icontains=q)
        )
    work_orders = work_orders.order_by('-created_at')
    return render(request, 'production/wo_list.html', {
        'work_orders': work_orders,
        'q': q,
    })


def wo_detail(request, pk):
    work_order = get_object_or_404(WorkOrder, pk=pk)
    wo_items = work_order.items.all() if hasattr(work_order, 'items') else []
    return render(request, 'production/wo_view.html', {
        'work_order': work_order,
        'wo_items': wo_items,
    })