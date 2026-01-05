from django import forms
from .models import StockOut, StockIn, BankTransaction, OwnerDrawing, BankAccount

class SaleForm(forms.ModelForm):
    class Meta:
        model = StockOut
        fields = ['product', 'quantity', 'selling_price', 'payment_method', 'bank_account', 'reference']
        widgets = {
             # Hide bank_account initially or let user leave blank if Cash
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        bank_account = cleaned_data.get('bank_account')

        if payment_method == 'transfer' and not bank_account:
            self.add_error('bank_account', 'Bank Account is required for Transfer payments.')
            
        return cleaned_data

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")

        if product and quantity:
            if quantity > product.quantity:
                raise forms.ValidationError(
                    f"Only {product.quantity} items available in stock."
                )

        return quantity

class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ['product', 'quantity', 'unit_cost', 'supplier', 'bank_account']
        widgets = {
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        labels = {
            'bank_account': 'Paid From Account (Optional)'
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

class BankTransactionForm(forms.ModelForm):
    class Meta:
        model = BankTransaction
        fields = ['bank_account', 'transaction_type', 'category', 'amount', 'description', 'reference']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class OwnerDrawingForm(forms.ModelForm):
    class Meta:
        model = OwnerDrawing
        fields = ['bank_account', 'amount', 'description', 'reference']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'description': forms.TextInput(attrs={'placeholder': 'e.g. Personal Withdrawal'}),
        }

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['name', 'balance']
        widgets = {
            'balance': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Initial Balance'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Main Chase Account'}),
        }
        labels = {
            'balance': 'Initial Balance',
            'name': 'Account Name'
        }

from .models import HistoricalSale

class HistoricalSaleForm(forms.ModelForm):
    class Meta:
        model = HistoricalSale
        fields = ['date', 'sku', 'product_name', 'quantity', 'unit_cost', 'selling_price', 'reference']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty <= 0:
            raise forms.ValidationError("Quantity must be positive.")
        return qty
