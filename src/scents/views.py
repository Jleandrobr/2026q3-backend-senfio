from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from scents.models import (
    Batch,
    Capsule,
    ExternalEvent,
    MuseumProfile,
    QualityCheck,
    Reservation,
    StatusChange,
    describe_actor,
    expire_reservation,
    record_status_change,
)
from scents.permissions import IsCurator, IsTechnician
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
    permission_classes = [IsCurator]


class CapsuleViewSet(viewsets.ModelViewSet):
    queryset = Capsule.objects.select_related("batch").all()
    serializer_class = CapsuleSerializer
    filterset_fields = ["status", "rarity"]
    permission_classes = [IsCurator]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        capsule = self.get_object()
        capsule.requires_manual_approval = False
        capsule.save(update_fields=["requires_manual_approval", "updated_at"])
        return Response(self.get_serializer(capsule).data)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        capsule = self.get_object()
        changes = capsule.status_changes.order_by("created_at")
        return Response(StatusChangeSerializer(changes, many=True).data)

    @action(detail=True, methods=["post"])
    def retire(self, request, pk=None):
        capsule = self.get_object()
        if capsule.status == Capsule.Status.RETIRED:
            return Response(
                {"detail": "Cápsula já está aposentada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record_status_change(
            capsule,
            Capsule.Status.RETIRED,
            actor=describe_actor(request),
            reason="aposentada pela curadoria",
        )
        return Response(self.get_serializer(capsule).data)


class ReservationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

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
            expire_reservation(reservation, reason="expirada ao tentar retirada após o prazo")
            return Response(
                {"detail": "Reserva expirada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if reservation.capsule.requires_manual_approval:
            return Response(
                {"detail": "Cápsula rara/única exige aprovação do curador antes da retirada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            reservation.status = Reservation.Status.CHECKED_OUT
            reservation.checked_out_at = now
            reservation.save(update_fields=["status", "checked_out_at"])
            record_status_change(
                reservation.capsule,
                Capsule.Status.CHECKED_OUT,
                actor=describe_actor(request, fallback=f"visitante: {reservation.visitor_name}"),
                reason=f"retirada por {reservation.visitor_name}",
            )
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

        with transaction.atomic():
            reservation.status = Reservation.Status.RETURNED
            reservation.returned_at = timezone.now()
            reservation.return_notes = notes
            reservation.save(update_fields=["status", "returned_at", "return_notes"])
            actor = describe_actor(request, fallback=f"visitante: {reservation.visitor_name}")

            if damaged:
                record_status_change(
                    reservation.capsule,
                    Capsule.Status.QUARANTINE,
                    actor=actor,
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
                    actor=actor,
                    reason="devolução sem dano",
                )

        return Response(self.get_serializer(reservation).data)


class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.select_related("capsule", "reservation").all()
    serializer_class = QualityCheckSerializer
    permission_classes = [IsTechnician]


class MuseumProfileViewSet(viewsets.ModelViewSet):
    queryset = MuseumProfile.objects.select_related("user").all()
    serializer_class = MuseumProfileSerializer
    permission_classes = [IsCurator]


class StatusChangeViewSet(viewsets.ReadOnlyModelViewSet):
    """Somente leitura: a trilha é criada por `record_status_change`, nunca pela API."""

    queryset = StatusChange.objects.select_related("capsule").all()
    serializer_class = StatusChangeSerializer


class ExternalMuseumWebhookView(APIView):
    def post(self, request):
        serializer = ExternalEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        capsule = None
        if data["event_type"] == "capsule.quarantined":
            capsule_id = data.get("payload", {}).get("capsule_id")
            capsule = Capsule.objects.filter(pk=capsule_id).first()

            if capsule is None:
                return Response(
                    {"detail": "Não corresponde a nenhuma cápsula."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            event, created = ExternalEvent.objects.get_or_create(
                source=data["source"],
                event_id=data["event_id"],
                defaults={
                    "event_type": data["event_type"],
                    "payload": data.get("payload", {}),
                    "processed_at": timezone.now(),
                },
            )

            if created and capsule is not None:
                capsule = Capsule.objects.select_for_update().get(pk=capsule.pk)

                record_status_change(
                    capsule,
                    Capsule.Status.QUARANTINE,
                    actor="sistema (evento externo)",
                    reason=f"evento externo {event.source}:{event.event_id}",
                )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            ExternalEventSerializer(event).data,
            status=response_status,
        )


class CapsuleOccupancyReportView(APIView):
    def get(self, request):
        counts = {
            row["status"]: row["count"]
            for row in Capsule.objects.values("status").annotate(count=Count("id")).order_by()
        }
        report = {choice: counts.get(choice, 0) for choice, _ in Capsule.Status.choices}
        return Response(report)
