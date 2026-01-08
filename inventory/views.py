from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from decimal import Decimal
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import Product, Sale, StockIn, BankAccount, BankTransaction, OwnerDrawing
from .forms import SaleForm, StockInForm, BankTransactionForm, OwnerDrawingForm, HistoricalSaleForm, BankAccountForm

class CustomLoginView(LoginView):
    template_name = 'inventory/login.html'

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    products = Product.objects.all()
    
    # Financial Aggregation (Unified: Normal + Historical)
    financial_data = Sale.objects.aggregate(
        total_revenue=Sum(F('selling_price') * F('quantity')),
        total_profit=Sum('profit')
    )
    
    total_sales = financial_data['total_revenue'] or Decimal('0.00')
    total_profit = financial_data['total_profit'] or Decimal('0.00')

    # Bank Balance Summary
    bank_accounts = BankAccount.objects.all()
    total_bank_balance = sum(acc.balance for acc in bank_accounts)
    
    drawings_data = OwnerDrawing.objects.aggregate(total=Sum('amount'))
    total_drawings = drawings_data['total'] or Decimal('0.00')
    
    total_products = products.count()
    total_stock = products.aggregate(total=Sum('quantity'))['total'] or 0
    total_inventory_value = sum(p.quantity * p.average_cost for p in products)
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_stock': total_stock,
        'total_inventory_value': total_inventory_value,
        'total_sales': total_sales,
        'total_profit': total_profit,
        'bank_accounts': bank_accounts,
        'total_bank_balance': total_bank_balance,
        'total_drawings': total_drawings,
    }

    return render(request, 'inventory/dashboard.html', context)

@login_required
def bank_dashboard(request):
    accounts = BankAccount.objects.all()
    # Get recent transactions
    recent_transactions = BankTransaction.objects.select_related('bank_account').order_by('-date')[:50]
    
    total_balance = sum(a.balance for a in accounts)

    return render(request, 'inventory/bank_dashboard.html', {
        'accounts': accounts,
        'recent_transactions': recent_transactions,
        'total_balance': total_balance
    })

@login_required
def add_bank_account(request):
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bank_dashboard')
    else:
        form = BankAccountForm()
    return render(request, 'inventory/add_bank_account.html', {'form': form})

@login_required
def add_bank_transaction(request):
    if request.method == 'POST':
        form = BankTransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bank_dashboard')
    else:
        form = BankTransactionForm()
    return render(request, 'inventory/add_bank_transaction.html', {'form': form})

@login_required
def add_owner_drawing(request):
    if request.method == 'POST':
        form = OwnerDrawingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = OwnerDrawingForm()
    return render(request, 'inventory/add_owner_drawing.html', {'form': form})

@login_required
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()  # signals will auto-update stock
            return redirect('dashboard')
    else:
        form = SaleForm()

    return render(request, 'inventory/add_sale.html', {'form': form})

@login_required
def add_stock(request):
    if request.method == 'POST':
        form = StockInForm(request.POST)
        if form.is_valid():
            form.save()  # signals increase stock
            return redirect('dashboard')
    else:
        form = StockInForm()

    return render(request, 'inventory/add_stock.html', {'form': form})

# ---------------------------------------------------------
# HISTORICAL / LEGACY SALES
# ---------------------------------------------------------


@login_required
def historical_sales_list(request):
    sales = Sale.objects.filter(is_historical=True).order_by('-created_at')
    
    stats = sales.aggregate(
        total_revenue=Sum(F('selling_price') * F('quantity')),
        total_profit=Sum('profit')
    )
    
    return render(request, 'inventory/historical_sales_list.html', {
        'sales': sales,
        'total_revenue': stats['total_revenue'] or 0,
        'total_profit': stats['total_profit'] or 0,
    })

@login_required
def add_historical_sale(request):
    if request.method == 'POST':
        form = HistoricalSaleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('historical_sales_list')
    else:
        form = HistoricalSaleForm()
    
    return render(request, 'inventory/add_historical_sale.html', {'form': form})

