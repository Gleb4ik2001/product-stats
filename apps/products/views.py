from django.http import HttpRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db.models import Avg, Round

from .models import Product
from .serializers import ProductSerializer
from .services import CACHE_KEY_AVG_PRICE


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListView(APIView):
    """
    GET /items
    Выдача списка товаров с поддержкой:
    - Фильтрации по категории (category)
    - Фильтрации по диапозону цен (price_min, price_max)
    - Пагинации (page, page_size)
    """

    def get(self, request):
        queryset = Product.objects.all()

        category = request.query_params.get('category')
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')

        if category:
            queryset = queryset.filter(category__iexact=category.strip())

        try:
            if price_min is not None:
                queryset = queryset.filter(price__gte=float(price_min))
            if price_max is not None:
                queryset = queryset.filter(price__lte=float(price_max))
        except ValueError:
            return Response(
                {"error": "Параметры price_min и price_max должны быть валидными числами."},
                status=status.HTTP_400_BAD_REQUEST
            )

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AvgPriceByCategoryView(APIView):
    """
    GET /stats/avg-price-by-category
    Выдача агрегированной средней цены по категориям.
    Результат кэшируется в Redis на 10 минут (600 сек).
    """

    def get(self, request: HttpRequest):
        # Пробуем получить из кэша
        try:
            cached_stats = cache.get(CACHE_KEY_AVG_PRICE)
            if cached_stats is not None:
                return Response({
                    "source": "cache",
                    "data": cached_stats
                }, status=status.HTTP_200_OK)
        except Exception:
            # Если кэша нет — считаем агрегат средствами ORM
            stats = (
                Product.objects.values('category')
                .annotate(avg_price=Round(Avg('price'), 2))
                .order_by('category')
            )

            result = {item['category']: float(item['avg_price']) for item in stats}

            # Записываем в кэш Redis (600 секунд)
            cache.set(CACHE_KEY_AVG_PRICE, result, timeout=600)

            return Response({
                "source": "database",
                "data": result
            }, status=status.HTTP_200_OK)