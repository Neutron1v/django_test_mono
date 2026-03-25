from django.db import models


class TrackedCurrency(models.Model):
    # 840 = USD, 978 = EUR тощо (ISO 4217)
    iso_numeric_code = models.PositiveIntegerField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["iso_numeric_code"]
        verbose_name = "Валюта (відстеження)"
        verbose_name_plural = "Валюти (відстеження)"

    def __str__(self):
        return str(self.iso_numeric_code)


class ExchangeRateRecord(models.Model):
    # Один запит з Monobank: скільки коштує валюта в гривнях
    currency_code = models.PositiveIntegerField(db_index=True)
    api_timestamp = models.DateTimeField(db_index=True)
    rate_buy = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    rate_sell = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    rate_cross = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-api_timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["currency_code", "api_timestamp"],
                name="uniq_exchange_rate_currency_api_ts",
            )
        ]
        indexes = [
            models.Index(fields=["currency_code", "-api_timestamp"]),
        ]
        verbose_name = "Курс (архів)"
        verbose_name_plural = "Курси (архів)"

    def __str__(self):
        return f"{self.currency_code} @ {self.api_timestamp}"
