from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from scents.models import (
    Batch,
    Capsule,
    MuseumProfile,
    QualityCheck,
    Reservation,
    StatusChange,
    record_status_change,
)
from scents.permissions import IsCurator
from scents.serializers import (
    BatchSerializer,
    CapsuleSerializer,
    ExternalEventSerializer,
    MuseumProfileSerializer,
    QualityCheckSerializer,
    ReservationSerializer,
    ReturnReservationSerializer,
    StatusChangeSerializer,
)


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class CapsuleViewSet(viewsets.ModelViewSet):
    queryset = Capsule.objects.select_related("batch").all()
    serializer_class = CapsuleSerializer
    filterset_fields = ["status", "rarity"]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("capsule", "capsule__batch").all()
    serializer_class = ReservationSerializer

    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        reservation = self.get_object()
        now = timezone.now()

        if reservation.status != Reservation.Status.PENDING:
            return Response(
                {"detail": "Somente reservas pendentes podem ser retiradas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reservation.pickup_deadline < now:
            reservation.status = Reservation.Status.EXPIRED
            reservation.capsule.status = Capsule.Status.AVAILABLE
            reservation.save(update_fields=["status"])
            reservation.capsule.save(update_fields=["status", "updated_at"])
            return Response(
                {"detail": "Reserva expirada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Reservation.Status.CHECKED_OUT
        reservation.checked_out_at = now
        reservation.capsule.status = Capsule.Status.CHECKED_OUT
        reservation.save(update_fields=["status", "checked_out_at"])
        reservation.capsule.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["post"], url_path="return")
    def return_capsule(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status != Reservation.Status.CHECKED_OUT:
            return Response(
                {"detail": "Somente reservas retiradas podem ser devolvidas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReturnReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        damaged = serializer.validated_data["damaged"]
        notes = serializer.validated_data["notes"]

        reservation.status = Reservation.Status.RETURNED
        reservation.returned_at = timezone.now()
        reservation.return_notes = notes
        reservation.save(update_fields=["status", "returned_at", "return_notes"])

        if damaged:
            record_status_change(
                reservation.capsule,
                Capsule.Status.QUARANTINE,
                reason="devolução com dano",
            )

            QualityCheck.objects.create(
                capsule=reservation.capsule,
                reservation=reservation,
                inspector_name="Sistema",
                result=QualityCheck.Result.DAMAGED,
                notes=notes,
            )
        else:
            record_status_change(
                reservation.capsule,
                Capsule.Status.AVAILABLE,
                reason="devolução sem dano",
            )

        return Response(self.get_serializer(reservation).data)


class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.select_related("capsule", "reservation").all()
    serializer_class = QualityCheckSerializer


class MuseumProfileViewSet(viewsets.ModelViewSet):
    queryset = MuseumProfile.objects.select_related("user").all()
    serializer_class = MuseumProfileSerializer
    permission_classes = [IsCurator]


class StatusChangeViewSet(viewsets.ModelViewSet):
    queryset = StatusChange.objects.select_related("capsule").all()
    serializer_class = StatusChangeSerializer


class ExternalMuseumWebhookView(APIView):
    def post(self, request):
        serializer = ExternalEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save(processed_at=timezone.now())

        if event.event_type == "capsule.quarantined":
            capsule_id = event.payload.get("capsule_id")
            Capsule.objects.filter(id=capsule_id).update(status=Capsule.Status.QUARANTINE)

        return Response(ExternalEventSerializer(event).data, status=status.HTTP_201_CREATED)
