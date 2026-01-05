from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sales/add/', views.add_sale, name='add_sale'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('bank/', views.bank_dashboard, name='bank_dashboard'),
    path('bank/account/add/', views.add_bank_account, name='add_bank_account'),
    path('bank/add/', views.add_bank_transaction, name='add_bank_transaction'),
    path('owner/draw/', views.add_owner_drawing, name='add_owner_drawing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('history/', views.historical_sales_list, name='historical_sales_list'),
    path('history/add/', views.add_historical_sale, name='add_historical_sale'),
]
