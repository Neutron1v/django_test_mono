import logging

from celery import shared_task

from currencies.services import store_uah_rates_from_monobank

logger = logging.getLogger(__name__)


@shared_task(
    name="currencies.tasks.fetch_and_store_monobank_rates",
    ignore_result=False,
)
def fetch_and_store_monobank_rates():
    how_many = store_uah_rates_from_monobank()
    logger.info("Monobank: збережено %s рядків", how_many)
    return how_many
