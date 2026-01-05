from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import StockIn, StockOut
from decimal import Decimal

@receiver(post_save, sender=StockIn)
def process_stock_in(sender, instance, created, **kwargs):
    """
    When stock adds:
    1. Calculate new Weighted Average Cost
    2. Increase Product Quantity
    """
    if created:
        product = instance.product
        
        # WE MUST HANDLE THE MATH CAREFULLY
        # Incoming Value = Qty * Unit Cost
        # Current Value = Current Qty * Current Current Avg Cost
        # New Qty = Current Qty + Incoming Qty
        # New Avg = (Current Value + Incoming Value) / New Qty
        
        current_qty = product.quantity
        current_avg = product.average_cost
        
        incoming_qty = instance.quantity
        incoming_cost = instance.unit_cost
        
        total_current_value = current_qty * current_avg
        total_incoming_value = incoming_qty * incoming_cost
        
        new_total_qty = current_qty + incoming_qty
        
        if new_total_qty > 0:
            new_average_cost = (total_current_value + total_incoming_value) / new_total_qty
        else:
            new_average_cost = Decimal('0.00')
            
        # Update Product
        product.average_cost = new_average_cost
        product.quantity = new_total_qty
        product.save()

@receiver(pre_save, sender=StockOut)
def lock_cost_basis(sender, instance, **kwargs):
    """
    BEFORE saving a sale:
    1. Lock in the current Product Average Cost as 'cost_at_sale'
    """
    if not instance.pk:  # Only on creation (new sale)
        product = instance.product
        # We lock the cost NOW, so future price changes don't affect this sale's profit record
        instance.cost_at_sale = product.average_cost

@receiver(post_save, sender=StockOut)
def process_stock_out(sender, instance, created, **kwargs):
    """
    When stock leaves:
    1. Decrease Product Quantity
    2. If Transfer, add to Bank Balance
    """
    if created:
        product = instance.product
        if product.quantity >= instance.quantity:
            product.quantity -= instance.quantity
            product.save()
        else:
            product.quantity = 0 
            product.save()
            
        # Bank Logic
        if instance.payment_method == 'transfer' and instance.bank_account:
            BankTransaction.objects.create(
                bank_account=instance.bank_account,
                transaction_type='in',
                category='sale',
                amount=instance.total_sale(),
                description=f"Sale Ref: {instance.reference or 'N/A'}",
                reference=instance.reference,
                date=instance.date
            )

# ---------------------------------------------------------
# NEW BANKING SIGNALS
# ---------------------------------------------------------

from .models import BankAccount, BankTransaction, OwnerDrawing

@receiver(post_save, sender=BankTransaction)
def update_bank_balance(sender, instance, created, **kwargs):
    """
    Update BankAccount balance when a transaction is saved.
    Note: Ideally we should handle updates/deletes too, but for now we focus on creation.
    """
    if created:
        account = instance.bank_account
        if instance.transaction_type == 'in':
            account.balance += instance.amount
        elif instance.transaction_type == 'out':
            account.balance -= instance.amount
        account.save()

@receiver(post_save, sender=StockIn)
def create_transaction_from_stock_in(sender, instance, created, **kwargs):
    """
    If a Bank Account was selected for purchase, deduct money.
    """
    if created and instance.bank_account:
        # Calculate total cost
        total_cost = instance.quantity * instance.unit_cost
        
        BankTransaction.objects.create(
            bank_account=instance.bank_account,
            transaction_type='out',
            category='inventory',
            amount=total_cost,
            description=f"Stock Purchase: {instance.product.name}",
            reference=f"StockIn #{instance.pk}",
            date=instance.date
        )

@receiver(post_save, sender=OwnerDrawing)
def create_transaction_from_drawing(sender, instance, created, **kwargs):
    """
    When OwnerDrawing is created, create a corresponding BankTransaction (Withdrawal).
    Logic:
    1. Create BankTransaction (which triggers update_bank_balance)
    2. Link it back to OwnerDrawing
    """
    if created and not instance.bank_transaction:
        transaction = BankTransaction.objects.create(
            bank_account=instance.bank_account,
            transaction_type='out',
            category='owner_draw',
            amount=instance.amount,
            description=f"Owner Drawing: {instance.description}",
            reference=instance.reference,
            date=instance.date
        )
        instance.bank_transaction = transaction
        instance.save()

# ---------------------------------------------------------
# INITIAL SETUP SIGNALS
# ---------------------------------------------------------
from django.db.models.signals import post_migrate
from django.contrib.auth.models import User
from django.apps import apps

@receiver(post_migrate)
def create_initial_user(sender, **kwargs):
    """
    Ensure the 'helmet' user exists after every migrate.
    Password: helmet@2025
    """
    # Only run for the inventory app to avoid running multiple times
    if sender.name != 'inventory':
        return

    User = apps.get_model('auth', 'User')
    username = 'helmet'
    if not User.objects.filter(username=username).exists():
        print(f"Creating default user: {username}")
        User.objects.create_superuser(username, 'admin@example.com', 'helmet@2025')
    else:
        pass

