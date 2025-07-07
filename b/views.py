from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from .models import Supplier, Purchase, Medicine, Batch, Sale, SaleItem
from django.utils import timezone
from django.db.models import Sum, F
from datetime import datetime, timedelta
from django.contrib import messages
# Create your views here.
def calculate_percentage_change(current, previous):
    if previous == 0:
        return None if current == 0 else 100.0
    return ((current - previous) / previous) * 100

def index(request):
    # Handle date filtering from GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = timezone.now().date()

    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            start_date = today
            end_date = today
    except ValueError:
        start_date = today
        end_date = today

    yesterday = today - timedelta(days=1)
    current_month = today.month
    current_year = today.year

    # Total Products
    total_products = Medicine.objects.count()
    total_products_prev = Medicine.objects.filter(
        id__in=Batch.objects.filter(
            purchase__purchase_date__lt=today
        ).values_list('medicine_id', flat=True)
    ).distinct().count()
    total_products_change = calculate_percentage_change(total_products, total_products_prev)

    # Low Stock
    low_stock_batches = Batch.objects.filter(
        quantity_remaining__lt=F('medicine__min_quantity')
    ).select_related('medicine')
    low_stock_count = low_stock_batches.count()
    low_stock_prev = Batch.objects.filter(
        quantity_remaining__lt=F('medicine__min_quantity'),
        purchase__purchase_date__lt=today
    ).count()
    low_stock_change = calculate_percentage_change(low_stock_count, low_stock_prev)

    # Today's Sales and Profit
    todays_sales = Sale.objects.filter(date__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    yesterdays_sales = Sale.objects.filter(date__date=yesterday).aggregate(total=Sum('total_amount'))['total'] or 0
    todays_sales_change = calculate_percentage_change(todays_sales, yesterdays_sales)

    todays_profit = Sale.objects.filter(date__date=today).aggregate(total=Sum('profit'))['total'] or 0
    yesterdays_profit = Sale.objects.filter(date__date=yesterday).aggregate(total=Sum('profit'))['total'] or 0
    todays_sales_change_profit = calculate_percentage_change(todays_profit, yesterdays_profit)

    # Monthly Revenue
    monthly_revenue = Sale.objects.filter(
        date__year=current_year, date__month=current_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    last_month = today.replace(day=1) - timedelta(days=1)
    last_month_revenue = Sale.objects.filter(
        date__year=last_month.year, date__month=last_month.month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    monthly_revenue_change = calculate_percentage_change(monthly_revenue, last_month_revenue)

    monthly_revenue_profit = Sale.objects.filter(
        date__year=current_year, date__month=current_month
    ).aggregate(total=Sum('profit'))['total'] or 0
    last_month_profit = Sale.objects.filter(
        date__year=last_month.year, date__month=last_month.month
    ).aggregate(total=Sum('profit'))['total'] or 0
    monthly_revenue_change_profit = calculate_percentage_change(monthly_revenue_profit, last_month_profit)

    # Annual Sales
    annual_sales_total = Sale.objects.filter(date__year=current_year).aggregate(total=Sum('total_amount'))['total'] or 0
    annual_sales_profit = Sale.objects.filter(date__year=current_year).aggregate(total=Sum('profit'))['total'] or 0

    # Filtered range sales and profit
    range_sales_total = Sale.objects.filter(date__date__range=(start_date, end_date)).aggregate(total=Sum('total_amount'))['total'] or 0
    range_sales_profit = Sale.objects.filter(date__date__range=(start_date, end_date)).aggregate(total=Sum('profit'))['total'] or 0

    # Recent Transactions
    recent_purchases = Purchase.objects.select_related('distributor').order_by('-purchase_date')[:3]
    recent_sales = Sale.objects.order_by('-date')[:3]
    transactions = [
        {
            'type': 'purchase',
            'name': f"Purchase from {p.distributor.name}",
            'time': timezone.make_aware(datetime.combine(p.purchase_date, datetime.min.time())),
            'amount': p.total_amount
        } for p in recent_purchases
    ] + [
        {
            'type': 'sale',
            'name': f"Sale to {s.customer_name}",
            'time': s.date,
            'amount': s.total_amount
        } for s in recent_sales
    ]
    transactions.sort(key=lambda x: x['time'], reverse=True)
    recent_transactions = transactions[:3]
    return render(request, 'index.html', {
        'total_products': total_products,
        'total_products_change': total_products_change,
        'low_stock_batches': low_stock_batches,
        'low_stock_count': low_stock_count,
        'low_stock_change': low_stock_change,
        'todays_sales_total': todays_sales,
        'todays_sales_change': todays_sales_change,
        'todays_sales_total_profit': todays_profit,
        'todays_sales_change_profit': todays_sales_change_profit,
        'monthly_revenue': monthly_revenue,
        'monthly_revenue_change': monthly_revenue_change,
        'monthly_revenue_profit': monthly_revenue_profit,
        'monthly_revenue_change_profit': monthly_revenue_change_profit,
        'annual_sales_total': annual_sales_total,
        'annual_sales_profit': annual_sales_profit,
        'range_sales_total': range_sales_total,
        'range_sales_profit': range_sales_profit,
        'recent_transactions': recent_transactions,
        'selected_start_date': start_date,
        'selected_end_date': end_date,
    })

def purchase(request): 
    medicines = Medicine.objects.all()
    if request.method == 'POST':
        print(request.POST)
        supplier = request.POST.get('supplier')
        sname, _ = Supplier.objects.get_or_create(name=supplier)
        invoice_number = request.POST.get('invoiceNumber')
        purchase_date = request.POST.get('purchaseDate')
        gst =request.POST.get('gst') if request.POST.get('gst') else 0
        discount =request.POST.get('discount') if request.POST.get('discount') else 0
        sub_total =request.POST.get('subTotal') if request.POST.get('subTotal') else 0
        total_amount =request.POST.get('grandTotal') if request.POST.get('grandTotal') else 0

        purchase = Purchase.objects.create(
            distributor=sname,
            invoice_number=invoice_number,
            purchase_date=purchase_date,
            gst=gst,
            discount=discount,
            sub_total=sub_total,
            total_amount=total_amount
        )

        products = []
        i = 0
        while f'products[{i}].name' in request.POST:
            medicine_name = request.POST.get(f'products[{i}].name')
            medicine = Medicine.objects.filter(name=medicine_name).first()
            if not medicine:
                print("medicine not found")
                medicine = Medicine.objects.create(name=medicine_name, min_quantity=10)
            quantity = int(request.POST.get(f'products[{i}].strips', 0)) * int(request.POST.get(f'products[{i}].boxes', 0)) * int(request.POST.get(f'products[{i}].tablets', 0))
            products.append({
                'purchase': purchase,
                'medicine': medicine,
                'batch_code': request.POST.get(f'products[{i}].batchCode'),
                'strips': request.POST.get(f'products[{i}].strips'),
                'tablets': request.POST.get(f'products[{i}].tablets'),
                'boxes': request.POST.get(f'products[{i}].boxes'),
                'rate': request.POST.get(f'products[{i}].rate'),
                'cost_price': request.POST.get(f'products[{i}].amount'),
                'mrp': request.POST.get(f'products[{i}].mrp'),
                'hsn_code': request.POST.get(f'products[{i}].hsn') or '-',  # fallback to '-'
                'expiry_date': request.POST.get(f'products[{i}].expiry') or '2003-11-20',
                'quantity': quantity,
                'quantity_remaining': quantity


            })
            i += 1

        for product in products:
            print(product)
            Batch.objects.create(**product)

        return redirect('purchase')  # Prevent form resubmission
    purchases = Purchase.objects.all().order_by('-purchase_date')
    paginator = Paginator(purchases, 7)  # Show 7 purchases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    recent_purchases = []
    for purchase in page_obj:
        supplier = purchase.distributor
        batches = Batch.objects.filter(purchase=purchase)
        total_items = batches.count()

        recent_purchases.append({
            'id': purchase.id,
            'invoice_number': purchase.invoice_number,
            'purchase_date': purchase.purchase_date,
            'total_amount': purchase.total_amount,
            'supplier': supplier.name,
            'total_items': total_items,
        })

    return render(request, 'purchase.html', {
        'medicines': medicines,
        'recent_purchases': recent_purchases,
        'page_obj': page_obj,  # Pass for pagination controls
    })

def sales(request):
    if request.method == 'POST':
        try:
            print(request.POST)
            data = request.POST
            product_names = data.getlist('product_name[]')
            quantities = data.getlist('quantity[]')
            unit_prices = data.getlist('unit_price[]')
            totals = data.getlist('total[]')
            refered_doctor = data.get('refered_doctor')
            mobile = data.get('mobile')
            gst = data.get('gst')
            discount = data.get('discount')
            subtotal = data.get('subtotal')
            grandtotal = data.get('grandtotal')

            with transaction.atomic():
                sale = Sale.objects.create(
                    customer_name=data.get('customer_name'),
                    date=data.get('date'),
                    refered_doctor=refered_doctor,
                    mobile=mobile,
                    sub_total=subtotal,
                    gst=gst,
                    discount=discount,
                    total_amount=grandtotal,
                    profit=0
                )

                total_profit = 0

                for product_name, quantity_str, unit_price_str, total in zip(product_names, quantities, unit_prices, totals):
                    medicine = get_object_or_404(Medicine, name=product_name)
                    quantity_needed = int(quantity_str)
                    unit_price = float(unit_price_str)

                    batches = Batch.objects.filter(
                        medicine=medicine,
                        quantity_remaining__gt=0
                    ).order_by('expiry_date')

                    if not batches.exists():
                        raise Exception(f"No stock available for {medicine.name}")

                    for batch in batches:
                        if quantity_needed <= 0:
                            break

                        take_quantity = min(batch.quantity_remaining, quantity_needed)

                        sale_item = SaleItem.objects.create(
                            sale=sale,
                            batch=batch,
                            quantity=take_quantity,
                            selling_price=unit_price
                        )
                        sale_item.save()

                        batch.quantity_remaining -= take_quantity
                        batch.save()

                        total_profit += sale_item.get_profit()
                        quantity_needed -= take_quantity

                    if quantity_needed > 0:
                        raise Exception(f"Not enough stock to fulfill {medicine.name}")

                sale.profit = total_profit
                sale.save()

            return redirect('sales')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('sales')



    # GET view logic
    all_sales = Sale.objects.order_by('-date')
    paginator = Paginator(all_sales, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sales_data = []
    for sale in page_obj:
        items = sale.items.select_related('batch__medicine')
        for item in items:
            print(item)
        medicine_names = [item.batch.medicine.name for item in items]
        total_quantity = sum(item.quantity for item in items)

        sales_data.append({
            'id': sale.id,
            'date': sale.date.strftime('%Y-%m-%d'),
            'customer_name': sale.customer_name,
            'medicine_list': ', '.join(medicine_names[:3]) + ('...' if len(medicine_names) > 3 else ''),
            'total_items': total_quantity,
            'total_price': sale.total_amount,
        })

    return render(request, 'sales.html', {
        'sales_data': sales_data,
        'page_obj': page_obj,
    })
def get_products(request):
    term = request.GET.get('term', '')
    products = Medicine.objects.filter(name__icontains=term)[:10]
    data = [{'id': p.id, 'name': p.name} for p in products]
    return JsonResponse(data, safe=False)

def purchase_details(request, pk):
    purchase = Purchase.objects.get(pk=pk)
    batches = purchase.batches.select_related('medicine').all()

    return JsonResponse({
        "distributor": purchase.distributor.name,
        "invoice_number": purchase.invoice_number,
        "purchase_date": purchase.purchase_date.strftime('%Y-%m-%d'),
        "gst": str(purchase.gst),
        "discount": str(purchase.discount),
        "sub_total": str(purchase.sub_total),
        "total_amount": str(purchase.total_amount),
        "batches": [{
            "medicine": batch.medicine.name,
            "batch_code": batch.batch_code,
            "quantity": batch.quantity,
            "cost_price": str(batch.cost_price),
            "mrp": str(batch.mrp),
            "expiry_date": batch.expiry_date.strftime('%Y-%m-%d'),
        } for batch in batches]
    })

def sale_details(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.select_related('batch__medicine')

    sale_data = {
        "customer_name": sale.customer_name,
        "date": sale.date.strftime("%Y-%m-%d %H:%M"),
        "gst": str(sale.gst),
        "discount": str(sale.discount),
        "sub_total": str(sale.sub_total),
        "total_amount": str(sale.total_amount),
        "mobile": sale.mobile,
        "referred_doctor": sale.refered_doctor,
        "bill_number": sale.id,
        "batches": []
    }

    for item in items:
        batch = item.batch
        cost_price = item.get_cost()
        sale_data["batches"].append({  
            "medicine": batch.medicine.name,
            "batch_code": batch.batch_code,
            "quantity": item.quantity,
            "single_price": f"{item.selling_price:.3f}",
            "selling_price": f"{(item.quantity * item.selling_price):.3f}",
            "cost_price": f"{cost_price:.3f}",
            "expiry_date": batch.expiry_date.strftime("%Y-%m-%d"),
        })

    return JsonResponse(sale_data, encoder=DjangoJSONEncoder)

def get_batch_info(request, medicine_id):
    batch = (
        Batch.objects
        .filter(medicine_id=medicine_id, quantity_remaining__gt=0)
        .order_by('expiry_date')  # Closest to expiry first
        .first()
    )

    if batch:
        return JsonResponse({
            'mrp': float(batch.mrp),
            'strips': batch.strips,
            'tablets_per_strip': batch.tablets,
            'boxes': batch.boxes
        })
    else:
        print("No batch found or all expired")
    return JsonResponse({'error': 'No batch found or all expired'}, status=404)

def reports(request):
    transactions = []

    # Purchases
    for p in Purchase.objects.select_related('distributor'):
        transactions.append({
            'type': 'Purchase',
            'name': f"Purchase from {p.distributor.name}",
            'date': timezone.make_aware(datetime.combine(p.purchase_date, datetime.min.time())),
            'amount': p.total_amount,
        })

    # Sales
    for s in Sale.objects.all():
        transactions.append({
            'type': 'Sale',
            'name': f"Sale to {s.customer_name}",
            'date': s.date,
            'amount': s.total_amount,
        })

    # Sort by date descending
    transactions.sort(key=lambda x: x['date'], reverse=True)

    # Pagination
    paginator = Paginator(transactions, 7)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'report.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
    })



