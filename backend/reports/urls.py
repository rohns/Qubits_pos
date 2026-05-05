from django.urls import path
from . import views

urlpatterns = [
    path('daily-sales/',    views.daily_sales),
    path('payment-methods/', views.payment_methods),
    path('top-services/',   views.top_services),
    path('monthly-sales/',  views.monthly_sales),
    path('daily-expenses/', views.daily_expenses),
    path('profit-summary/', views.profit_summary),
    path('eod-summary/',    views.eod_summary),
]
