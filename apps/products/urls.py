from django.urls import path
from .views import ProductListView, AvgPriceByCategoryView


urlpatterns = [
    path('items/', ProductListView.as_view(), name='product-list'),
    path('stats/avg-price-by-category/', AvgPriceByCategoryView.as_view(), name='avg-price-by-category'),
]
