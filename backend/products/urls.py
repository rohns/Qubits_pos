from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StockMovementListView

router = DefaultRouter()
router.register('', ProductViewSet, basename='products')

urlpatterns = [
    path('stock-movements/', StockMovementListView.as_view()),
    path('', include(router.urls)),
]
