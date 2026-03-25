from pathlib import Path

from django.core.management.base import BaseCommand

from currencies.export_rates import tracked_currencies_to_dataframe
from currencies.models import TrackedCurrency


class Command(BaseCommand):
    help = "Зберегти таблицю відстежуваних валют і поточних курсів у CSV-файл."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default="currency_rates.csv",
            help="Куди зберегти файл.",
        )
        parser.add_argument(
            "--only-active",
            action="store_true",
            help="Тільки валюти з is_active=True.",
        )

    def handle(self, *args, **options):
        queryset = TrackedCurrency.objects.all()
        if options["only_active"]:
            queryset = queryset.filter(is_active=True)

        path = Path(options["output"]).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        table = tracked_currencies_to_dataframe(queryset)
        table.to_csv(path, index=False)

        self.stdout.write(self.style.SUCCESS(f"Готово, файл: {path}"))
