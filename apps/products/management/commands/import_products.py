from django.core.management.base import BaseCommand
from products.services import fetch_raw_data, process_and_normalize_data, import_products_to_db


class Command(BaseCommand):
    help = "Ручной запуск импорта и нормализации товаров из внешнего источника или sample_data.json"

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Необязательный HTTP/HTTPS URL источника данных (JSON)'
        )

    def handle(self, *args, **options):
        url = options.get('url')
        self.stdout.write(self.style.NOTICE("Запуск процесса импорта..."))

        try:
            raw_data = fetch_raw_data(url)
            df = process_and_normalize_data(raw_data)
            count = import_products_to_db(df)

            self.stdout.write(
                self.style.SUCCESS(f"Успешно обработано и сохранено записей: {count}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при импорте данных: {e}")
            )
