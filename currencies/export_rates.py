import pandas as pd

from currencies.models import ExchangeRateRecord, TrackedCurrency
from currencies.utils import get_currency_alpha


def tracked_currencies_to_dataframe(queryset):
    rows = []
    for currency in queryset.order_by("iso_numeric_code"):
        last = (
            ExchangeRateRecord.objects.filter(
                currency_code=currency.iso_numeric_code,
            )
            .order_by("-api_timestamp")
            .first()
        )
        rows.append(
            {
                "iso_numeric_code": currency.iso_numeric_code,
                "currency_alpha": get_currency_alpha(currency.iso_numeric_code)
                or "",
                "is_active": currency.is_active,
                "rate_buy": last.rate_buy if last else "",
                "rate_sell": last.rate_sell if last else "",
                "rate_cross": last.rate_cross if last else "",
                "api_timestamp": last.api_timestamp.isoformat() if last else "",
            }
        )
    return pd.DataFrame(rows)
