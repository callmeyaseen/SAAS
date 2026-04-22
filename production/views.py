from django.shortcuts import render, redirect, get_object_or_404
from .models import ProductionPlan, ProductionRoll
from sale.models import SaleOrder
from utilities.models import Machine
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
    # Calculate total planned qty so far for this order
    already_planned = ProductionPlan.objects.filter(sale_order=so).aggregate(total=Sum('planned_qty'))['total'] or 0
    balance = so.order_qty - already_planned
    
    return JsonResponse({
        'order_qty': so.order_qty,
        'balance_qty': max(0, balance),
        'width_type': so.fabric_width_type,
        'width': so.fabric_width,
        'finishing': so.finishing_process,
        'status': so.status,
        'running_on': ProductionPlan.objects.filter(sale_order=so, status="Open").count()
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
    plans = ProductionPlan.objects.filter(machine=machine, status="Open").select_related('sale_order', 'sale_order__product').annotate(
        total_scanned=Sum('rolls__weight')
    )
    
    load_data = []
    for p in plans:
        scanned = p.total_scanned or 0
        load_data.append({
            'plan_no': p.plan_no,
            'order_no': p.sale_order.sale_order_no,
            'article_name': p.sale_order.product.product_name if p.sale_order.product else "N/A",
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
    ).select_related('sale_order', 'sale_order__product', 'machine')

    data = [{
        'plan_no': p.plan_no,
        'machine': f"{p.machine.machine_name} ({p.machine.machine_code})" if p.machine else "N/A",
        'article': p.sale_order.product.product_name if p.sale_order.product else "N/A",
        'planned_qty': p.planned_qty,
    } for p in plans]

    return JsonResponse({'plans': data})

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
    ).select_related('sale_order', 'sale_order__product', 'machine').order_by('status', '-id').first()

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
        'article': plan.sale_order.product.product_name if plan.sale_order.product else "N/A",
        'planned_qty': plan.planned_qty,
        'balance': round(max(0, plan.planned_qty - scanned), 2),
        'next_roll_no': next_roll_no,
        'rolls': rolls_data, # Send list of existing rolls
    })

def plan_create(request):
    sales = SaleOrder.objects.filter(status="Open")
    machines = Machine.objects.filter(is_active=True)
    next_plan_no = generate_plan_no()

    if request.method == "POST":
        machine_ids = request.POST.getlist('machine[]')
        planned_qtys = request.POST.getlist('planned_qty[]')
        start_dates = request.POST.getlist('start_date[]')
        end_dates = request.POST.getlist('end_date[]')
        m_statuses = request.POST.getlist('status[]')
        sale_order_id = request.POST.get('sale_order')
        so_status = request.POST.get('so_status')

        # Get base plan number to avoid duplicates in loop
        current_plan_no = generate_plan_no()

        # Duplication Check: Ek hi Sale Order ek hi machine par dobara plan na ho
        has_error = False
        for m_id in machine_ids:
            if m_id and ProductionPlan.objects.filter(sale_order_id=sale_order_id, machine_id=m_id).exists():
                m_obj = Machine.objects.filter(id=m_id).first()
                messages.error(request, f"Duplicate Error: Machine {m_obj.machine_name if m_obj else m_id} is already planned for this Sale Order!")
                has_error = True
        
        if has_error:
            return render(request, 'production/plan_create.html', {
                'sales': sales, 
                'machines': machines, 
                'next_plan_no': next_plan_no
            })

        with transaction.atomic():
            # Update Sale Order Status
            so_obj = SaleOrder.objects.get(id=sale_order_id)
            so_obj.status = so_status
            so_obj.save()

            # Counter for plan sequence increment within the loop
            plan_prefix = current_plan_no.split('-')[0]
            plan_start_num = int(current_plan_no.split('-')[-1])

            for m_id, qty, s_date, e_date, m_stat in zip(machine_ids, planned_qtys, start_dates, end_dates, m_statuses):
                if m_id and qty:
                    p_no = f"{plan_prefix}-{plan_start_num:04d}"
                    ProductionPlan.objects.create(
                        plan_no=p_no,
                        sale_order_id=sale_order_id,
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
        'sales': sales,
        'machines': machines,
        'next_plan_no': next_plan_no
    })


def plan_edit(request, pk):
    plan = get_object_or_404(ProductionPlan, pk=pk)
    sales = SaleOrder.objects.all()
    machines = Machine.objects.filter(is_active=True)

    if request.method == "POST":
        # Update Plan Fields
        plan.machine_id = request.POST.get('machine')
        plan.planned_qty = request.POST.get('planned_qty')
        plan.start_date = request.POST.get('start_date')
        plan.end_date = request.POST.get('end_date')
        plan.status = request.POST.get('status')
        plan.remarks = request.POST.get('remarks')
        
        # Sale Order Status update (optional)
        so_status = request.POST.get('so_status')

        with transaction.atomic():
            plan.save()
            if so_status:
                plan.sale_order.status = so_status
                plan.sale_order.save()

        messages.success(request, f"Production Plan {plan.plan_no} updated successfully.")
        return redirect('production:plan_list')

    return render(request, 'production/plan_edit.html', {
        'plan': plan,
        'sales': sales,
        'machines': machines
    })


def plan_list(request):
    search_query = request.GET.get('search', '')
    plans = ProductionPlan.objects.all().order_by('-id')

    if search_query:
        plans = plans.filter(plan_no__icontains=search_query)

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