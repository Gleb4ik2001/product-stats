import pytest
import pandas as pd
from rest_framework.test import APIClient
from apps.products.models import Product
from apps.products.services import process_and_normalize_data, calculate_avg_price_pandas


@pytest.mark.django_db
class TestProductServiceAndAPI:

    # --- ТЕСТ 1: Парсинг и нормализация входных данных ---
    def test_data_normalization(self):
        raw_data = [
            {
                "external_id": "ext-1",
                "name": "  Phone  ",
                "category": "Gadgets",
                "price": " 200.5 ",
                "updated_at": "2026-07-24T12:00:00Z"
            },
            {
                "name": "Invalid Row",
                "category": "Gadgets",
                "price": "not_a_number",
                "updated_at": None
            }
        ]

        df = process_and_normalize_data(raw_data)

        # Невалидная строка должна быть отброшена
        assert len(df) == 1
        assert df.iloc[0]['name'] == 'Phone'
        assert df.iloc[0]['price'] == 200.5
        assert df.iloc[0]['external_id'] == 'ext-1'

    # --- ТЕСТ 2: Корректный расчет средней цены (Pandas) ---
    def test_avg_price_calculation(self):
        data = [
            {"category": "Electronics", "price": 100.0},
            {"category": "Electronics", "price": 200.0},
            {"category": "Furniture", "price": 50.0},
        ]
        df = pd.DataFrame(data)

        result = calculate_avg_price_pandas(df)

        assert result['Electronics'] == 150.0
        assert result['Furniture'] == 50.0

    # --- ТЕСТ 3: Фильтрация в API эндпоинте GET /api/items/ ---
    def test_api_filtering(self):
        client = APIClient()

        # Создаем тестовые записи
        Product.objects.create(
            external_id="1", name="Laptop", category="Electronics", price=1000.0, updated_at="2026-07-24T12:00:00Z"
        )
        Product.objects.create(
            external_id="2", name="Mouse", category="Electronics", price=25.0, updated_at="2026-07-24T12:00:00Z"
        )
        Product.objects.create(
            external_id="3", name="Chair", category="Furniture", price=150.0, updated_at="2026-07-24T12:00:00Z"
        )

        # Выполняем GET-запрос с фильтром по категории и минимальной цене
        response = client.get('/api/items/', {'category': 'Electronics', 'price_min': 50})

        assert response.status_code == 200
        data = response.json()['results']
        
        # Должен остаться только Laptop
        assert len(data) == 1
        assert data[0]['name'] == 'Laptop'
        assert data[0]['external_id'] == '1'