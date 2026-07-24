import logging
from typing import Optional
from celery import shared_task

from .services import fetch_raw_data, process_and_normalize_data, import_products_to_db

logger = logging.getLogger(__name__)


@shared_task(name="run_product_import_task")
def run_product_import_task(source_url: Optional[str] = None) -> str:
    """
    Фоновая задача Celery для периодического и идемпотентного импорта товаров.
    """
    logger.info("Старт планового импорта товаров через Celery...")

    raw_data = fetch_raw_data(source_url)
    if not raw_data:
        logger.warning("Нет данных для импорта.")
        return "No data fetched."

    df = process_and_normalize_data(raw_data)
    count = import_products_to_db(df)

    message = f"Импорт завершен успешно. Обработано/обновлено записей: {count}"
    logger.info(message)
    return message
