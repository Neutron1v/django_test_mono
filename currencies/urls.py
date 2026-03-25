from django.urls import include, path
from rest_framework.routers import DefaultRouter

from currencies.views import AvailableCurrenciesView, RateHistoryView, TrackedCurrencyViewSet

router = DefaultRouter()
router.register(r"tracked-currencies", TrackedCurrencyViewSet, basename="tracked-currency")

urlpatterns = [
    path("", include(router.urls)),
    path("currencies/available/", AvailableCurrenciesView.as_view(), name="currencies-available"),
    path("rates/history/", RateHistoryView.as_view(), name="rates-history"),
]
