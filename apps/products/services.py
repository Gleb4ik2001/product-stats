import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from django.core.cache import cache
from django.db import transaction

from .models import Product

logger = logging.getLogger(__name__)

CACHE_KEY_AVG_PRICE = "avg_price_by_category"


def fetch_raw_data(source_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Получение данных из публичного API.
    Если источник недоступен или не передан, читаем локальный sample_data.json.
    """
    if source_url:
        try:
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            logger.info(f"Данные успешно загружены из источника: {source_url}")
            return response.json()
        except Exception as exc:
            logger.warning(
                f"Не удалось получить данные по URL {source_url}: {exc}. "
                f"Переходим на резервный файл sample_data.json"
            )

    try:
        with open("sample_data.json", "r", encoding="utf-8") as f:
            logger.info("Загружаем данные из локального sample_data.json")
            return json.load(f)
    except FileNotFoundError:
        logger.error("Файл sample_data.json не найден!")
        return []


def process_and_normalize_data(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Обработка и нормализация данных с использованием Pandas.
    - Очистка от пробелов
    - Преобразование типов (price -> float, updated_at -> datetime)
    - Генерация external_id, если его нет во входных данных
    - Удаление строк с битыми обязательными полями
    """
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    # Проверяем минимальный набор необходимых полей
    required_cols = {"name", "category", "price", "updated_at"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Во входных данных отсутствуют обязательные поля: {missing}")

    # Нормализация текстовых полей
    df["name"] = df["name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()

    # Генерация external_id если его нет во внешнем источнике
    if "external_id" not in df.columns:
        df["external_id"] = None

    def ensure_external_id(row):
        val = row["external_id"]
        if pd.isna(val) or not str(val).strip():
            # Хэшируем name + category как fallback ключ
            raw_key = f"{row['name']}_{row['category']}".encode("utf-8")
            return hashlib.md5(raw_key).hexdigest()
        return str(val).strip()

    df["external_id"] = df.apply(ensure_external_id, axis=1)

    # Приведение типов и очистка ошибок
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    # Дропаем битые записи (где цена, дата, название или категория не валидны)
    initial_count = len(df)
    df = df.dropna(subset=["external_id", "name", "category", "price", "updated_at"])
    dropped_count = initial_count - len(df)

    if dropped_count > 0:
        logger.warning(f"Пропущено невалидных строк при нормализации: {dropped_count}")

    return df


def calculate_avg_price_pandas(df: pd.DataFrame) -> Dict[str, float]:
    """
    Чистый расчет средней цены по категориям средствами Pandas.
    (Пригодится как для локальной аналитики, так и для юнитов)
    """
    if df.empty:
        return {}

    grouped = df.groupby("category")["price"].mean().round(2)
    return grouped.to_dict()


def import_products_to_db(df: pd.DataFrame) -> int:
    """
    Идемпотентное сохранение/обновление записей в PostgreSQL.
    """
    if df.empty:
        logger.info("DataFrame пуст, сохранять нечего.")
        return 0

    imported_count = 0

    with transaction.atomic():
        for _, row in df.iterrows():
            dt = row["updated_at"].to_pydatetime()

            Product.objects.update_or_create(
                external_id=row["external_id"],
                defaults={
                    "name": row["name"],
                    "category": row["category"],
                    "price": row["price"],
                    "updated_at": dt,
                },
            )
            imported_count += 1

    # После успешного импорта сбрасываем кэш средних цен
    cache.delete(CACHE_KEY_AVG_PRICE)
    logger.info(f"Успешно обработано и сохранено записей в БД: {imported_count}")
    return imported_count
