from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=30)

    # Average Cost (Moving Weighted Average)
    # This replaces the static 'cost_price'
    average_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Average Unit Cost"
    )
    
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    # New: logic to track cost per batch
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost price per unit for this batch"
    )
    
    supplier = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"IN: {self.product.name} (+{self.quantity})"


class BankAccount(models.Model):
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} (${self.balance})"

class BankTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('in', 'In (Deposit)'),
        ('out', 'Out (Withdrawal)'),
    ]
    
    CATEGORIES = [
        ('sale', 'Sale Revenue'),
        ('inventory', 'Inventory Purchase'),
        ('expense', 'Business Expense'),
        ('owner_draw', 'Owner Drawing (Equity Withdrawal)'),
        ('owner_capital', 'Owner Capital Injection'),
        ('transfer', 'Internal Transfer'),
    ]

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} - {self.category} - {self.amount}"

class OwnerDrawing(models.Model):
    """
    Tracks money taken out by the owner.
    This is an EQUITY transaction, NOT an expense.
    It reduces Bank Balance but NOT Profit.
    """
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        help_text="Bank Account to withdraw from",
        null=True,
        blank=True
    )
    
    # Optional link if auto-generated
    bank_transaction = models.OneToOneField(
        BankTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='owner_drawing_record'
    )

    def __str__(self):
        return f"DRAWING: ${self.amount} ({self.date.strftime('%Y-%m-%d')})"

class StockIn(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    # New: logic to track cost per batch
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost price per unit for this batch"
    )
    
    supplier = models.CharField(max_length=100)
    
    # New: Link to bank account for immediate payment tracking
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Account used to pay for this stock"
    )
    
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"IN: {self.product.name} (+{self.quantity})"


class StockOut(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('transfer', 'Bank Transfer'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # New: Lock in the cost at the moment of sale
    # This is critical for accurate historical profit reports
    cost_at_sale = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=False, # Automatically set by system
        default=0.00
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )
    
    # New: Link to bank account for transfer payments
    bank_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Account receiving the payment (if Transfer)"
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    date = models.DateTimeField(auto_now_add=True)

    def total_sale(self):
        return self.quantity * self.selling_price

    def profit(self):
        # Profit = (Selling Price - Cost Basis) * Quantity
        current_cost = self.cost_at_sale
        return (self.selling_price - current_cost) * self.quantity
        
    def __str__(self):
        return f"OUT: {self.product.name} (-{self.quantity})"

class HistoricalSale(models.Model):
    """
    Stores legacy/manual sales data.
    COMPLETELY INDEPENDENT from Product inventory and Bank Balance.
    Used for historical reporting only.
    """
    date = models.DateField(help_text="Date of the original sale")
    sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original Cost Price per unit")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original Selling Price per unit")
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Old Invoice #")
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_revenue(self):
        return self.quantity * self.selling_price

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    @property
    def profit(self):
        return self.total_revenue - self.total_cost

    def __str__(self):
        return f"HIST: {self.product_name} ({self.date})"
