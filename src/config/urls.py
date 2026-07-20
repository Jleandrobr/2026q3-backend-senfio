from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from scents.views import (
    BatchViewSet,
    CapsuleOccupancyReportView,
    CapsuleViewSet,
    ExternalMuseumWebhookView,
    MuseumProfileViewSet,
    QualityCheckViewSet,
    ReservationViewSet,
    StatusChangeViewSet,
)

router = DefaultRouter()
router.register("batches", BatchViewSet)
router.register("capsules", CapsuleViewSet)
router.register("reservations", ReservationViewSet)
router.register("quality-checks", QualityCheckViewSet)
router.register("profiles", MuseumProfileViewSet)
router.register("status-changes", StatusChangeViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/webhooks/external-museum/", ExternalMuseumWebhookView.as_view()),
    path("api/reports/occupancy/", CapsuleOccupancyReportView.as_view()),
]
