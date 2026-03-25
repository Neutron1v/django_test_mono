from django.contrib import admin
from django.http import HttpResponse

from currencies.export_rates import tracked_currencies_to_dataframe
from currencies.models import ExchangeRateRecord, TrackedCurrency


@admin.register(TrackedCurrency)
class TrackedCurrencyAdmin(admin.ModelAdmin):
    list_display = ("iso_numeric_code", "is_active", "created_at")
    list_filter = ("is_active",)
    actions = ("export_rates_csv",)

    @admin.action(description="Завантажити CSV з курсами (обрані рядки)")
    def export_rates_csv(self, request, queryset):
        table = tracked_currencies_to_dataframe(queryset)
        csv_string = table.to_csv(index=False)
        response = HttpResponse(csv_string, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="currency_rates.csv"'
        return response


@admin.register(ExchangeRateRecord)
class ExchangeRateRecordAdmin(admin.ModelAdmin):
    list_display = (
        "currency_code",
        "api_timestamp",
        "rate_buy",
        "rate_sell",
        "rate_cross",
        "fetched_at",
    )
    list_filter = ("currency_code",)
    date_hierarchy = "api_timestamp"
