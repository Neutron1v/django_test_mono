from datetime import UTC, datetime

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from currencies.models import ExchangeRateRecord, TrackedCurrency
from currencies.serializers import (
    AvailableCurrencySerializer,
    ExchangeRateHistorySerializer,
    HistoryQuerySerializer,
    TrackedCurrencyCreateSerializer,
    TrackedCurrencySerializer,
    TrackedCurrencyToggleSerializer,
)
from currencies.services import fetch_monobank_currency_pairs, only_pairs_to_uah
from currencies.utils import get_currency_alpha


@extend_schema_view(
    list=extend_schema(summary="Список відстежуваних валют + поточний курс"),
    retrieve=extend_schema(summary="Одна валюта"),
    create=extend_schema(
        summary="Додати валюту до відстеження",
        request=TrackedCurrencyCreateSerializer,
        responses=TrackedCurrencySerializer,
    ),
    partial_update=extend_schema(
        summary="Увімкнути / вимкнути (is_active)",
        request=TrackedCurrencyToggleSerializer,
        responses=TrackedCurrencySerializer,
    ),
)
class TrackedCurrencyViewSet(viewsets.ModelViewSet):
    queryset = TrackedCurrency.objects.all().order_by("iso_numeric_code")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return TrackedCurrencyCreateSerializer
        if self.action in ("partial_update", "update"):
            return TrackedCurrencyToggleSerializer
        return TrackedCurrencySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_currency = serializer.save()
        output = TrackedCurrencySerializer(
            new_currency, context={"request": request}
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output = TrackedCurrencySerializer(instance, context={"request": request})
        return Response(output.data)


class AvailableCurrenciesView(APIView):
    @extend_schema(
        summary="Валюти з Monobank, яких ще немає у вашому списку",
        responses=AvailableCurrencySerializer(many=True),
    )
    def get(self, request):
        bank_data = fetch_monobank_currency_pairs()
        already_tracked = set(
            TrackedCurrency.objects.values_list("iso_numeric_code", flat=True)
        )

        answer = []
        for row in only_pairs_to_uah(bank_data):
            code = int(row["currencyCodeA"])
            if code in already_tracked:
                continue
            answer.append(
                {
                    "iso_numeric_code": code,
                    "currency_alpha": get_currency_alpha(code),
                    "rate_buy": row.get("rateBuy"),
                    "rate_sell": row.get("rateSell"),
                    "rate_cross": row.get("rateCross"),
                    "api_timestamp": datetime.fromtimestamp(int(row["date"]), tz=UTC),
                }
            )

        return Response(AvailableCurrencySerializer(answer, many=True).data)


class RateHistoryView(APIView):
    @extend_schema(
        summary="Історія курсу (тільки якщо валюта вже в списку відстеження)",
        parameters=[
            OpenApiParameter(
                name="currency",
                type=int,
                required=True,
                description="Числовий код ISO 4217",
            ),
            OpenApiParameter(
                name="date_from", type=str
            ),
            OpenApiParameter(name="date_to", type=str)
        ],
        responses=ExchangeRateHistorySerializer(many=True),
    )
    def get(self, request):
        params = HistoryQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)

        currency_code = params.validated_data["currency"]
        exists = TrackedCurrency.objects.filter(iso_numeric_code=currency_code).exists()
        if not exists:
            raise NotFound("Спочатку додай цю валюту до відстеження.")

        history = ExchangeRateRecord.objects.filter(currency_code=currency_code)

        if params.validated_data.get("date_from"):
            history = history.filter(
                api_timestamp__gte=params.validated_data["date_from"]
            )
        if params.validated_data.get("date_to"):
            history = history.filter(
                api_timestamp__lte=params.validated_data["date_to"]
            )

        history = history.order_by("-api_timestamp")[:5000]
        serializer = ExchangeRateHistorySerializer(history, many=True)
        return Response(serializer.data)
