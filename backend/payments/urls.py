from django.urls import path
from . import views

urlpatterns = [
    path('cash/', views.cash_payment),
    path('mpesa-cash/', views.mpesa_cash_payment),
    path('stk-push/', views.stk_push),
    path('mpesa-callback/', views.mpesa_callback),
    path('status/<str:checkout_request_id>/', views.payment_status),
]
