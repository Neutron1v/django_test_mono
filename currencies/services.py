from datetime import UTC, datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction

from currencies.models import ExchangeRateRecord, TrackedCurrency


def fetch_monobank_currency_pairs():
    response = requests.get(settings.MONOBANK_CURRENCY_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Monobank: очікувався список")
    return data


def only_pairs_to_uah(raw_list):
    uah = settings.UAH_ISO_NUMERIC
    out = []
    for item in raw_list:
        if item.get("currencyCodeB") != uah:
            continue
        if item.get("currencyCodeA") is None or item.get("date") is None:
            continue
        out.append(item)
    return out


@transaction.atomic
def store_uah_rates_from_monobank():
    tracked = set(
        TrackedCurrency.objects.filter(is_active=True).values_list(
            "iso_numeric_code", flat=True
        )
    )
    if not tracked:
        return 0


    fetched_now = datetime.now(tz=UTC)

    raw = fetch_monobank_currency_pairs()
    created = 0

    for item in only_pairs_to_uah(raw):
        code = int(item["currencyCodeA"])
        if code not in tracked:
            continue

        buy = item.get("rateBuy")
        sell = item.get("rateSell")
        cross = item.get("rateCross")

        #TODO : Треба це прибрати, юзав тільки щоб перевірити логіку зберігання без очікування оновлення рейтів в МОНО
        api_ts = datetime.fromtimestamp(int(item["date"]), tz=UTC).replace(
            microsecond=fetched_now.microsecond
        )
        _, is_created = ExchangeRateRecord.objects.update_or_create(
            currency_code=code,
            api_timestamp=api_ts,
            defaults={
                "rate_buy": None if buy is None else Decimal(str(buy)),
                "rate_sell": None if sell is None else Decimal(str(sell)),
                "rate_cross": None if cross is None else Decimal(str(cross)),
            },
        )
        created += 1 if is_created else 0

    return created
