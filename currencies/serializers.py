from rest_framework import serializers

from currencies.models import ExchangeRateRecord, TrackedCurrency
from currencies.services import fetch_monobank_currency_pairs, only_pairs_to_uah
from currencies.utils import get_currency_alpha


class TrackedCurrencySerializer(serializers.ModelSerializer):
    currency_alpha = serializers.SerializerMethodField()
    current_rate = serializers.SerializerMethodField()

    class Meta:
        model = TrackedCurrency
        fields = (
            "id",
            "iso_numeric_code",
            "currency_alpha",
            "is_active",
            "created_at",
            "current_rate",
        )
        read_only_fields = ("id", "created_at", "currency_alpha", "current_rate")

    def get_currency_alpha(self, obj):
        return get_currency_alpha(obj.iso_numeric_code)

    def get_current_rate(self, obj):
        last = (
            ExchangeRateRecord.objects.filter(currency_code=obj.iso_numeric_code)
            .order_by("-api_timestamp")
            .first()
        )
        if last is None:
            return {
                "rate_buy": None,
                "rate_sell": None,
                "rate_cross": None,
                "api_timestamp": None,
            }
        return {
            "rate_buy": last.rate_buy,
            "rate_sell": last.rate_sell,
            "rate_cross": last.rate_cross,
            "api_timestamp": last.api_timestamp,
        }


class TrackedCurrencyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackedCurrency
        fields = ("iso_numeric_code",)

    def validate_iso_numeric_code(self, value):
        if TrackedCurrency.objects.filter(iso_numeric_code=value).exists():
            raise serializers.ValidationError("Така валюта вже додана.")

        bank_json = fetch_monobank_currency_pairs()
        allowed_codes = {int(x["currencyCodeA"]) for x in only_pairs_to_uah(bank_json)}
        if value not in allowed_codes:
            raise serializers.ValidationError(
                "У Monobank зараз немає курсу цієї валюти до гривні."
            )
        return value


class TrackedCurrencyToggleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackedCurrency
        fields = ("is_active",)


class AvailableCurrencySerializer(serializers.Serializer):
    iso_numeric_code = serializers.IntegerField()
    currency_alpha = serializers.CharField(allow_null=True)
    rate_buy = serializers.DecimalField(
        max_digits=20, decimal_places=6, allow_null=True
    )
    rate_sell = serializers.DecimalField(
        max_digits=20, decimal_places=6, allow_null=True
    )
    rate_cross = serializers.DecimalField(
        max_digits=20, decimal_places=6, allow_null=True
    )
    api_timestamp = serializers.DateTimeField()


class ExchangeRateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRateRecord
        fields = (
            "id",
            "currency_code",
            "api_timestamp",
            "rate_buy",
            "rate_sell",
            "rate_cross",
            "fetched_at",
        )


class HistoryQuerySerializer(serializers.Serializer):
    currency = serializers.IntegerField(min_value=1)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        start = attrs.get("date_from")
        end = attrs.get("date_to")
        if start and end and start > end:
            raise serializers.ValidationError("date_from не може бути пізніше date_to.")
        return attrs
