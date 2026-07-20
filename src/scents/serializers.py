from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from scents.models import (
    Batch,
    Capsule,
    ExternalEvent,
    MuseumProfile,
    QualityCheck,
    Reservation,
    StatusChange,
    describe_actor,
    record_status_change,
)


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ["id", "code", "preservation_method", "produced_at", "expires_at", "notes"]


class CapsuleSerializer(serializers.ModelSerializer):
    batch_code = serializers.CharField(source="batch.code", read_only=True)

    class Meta:
        model = Capsule
        fields = [
            "id",
            "batch",
            "batch_code",
            "name",
            "scent_profile",
            "origin_story",
            "intensity",
            "rarity",
            "status",
            "expires_at",
            "requires_manual_approval",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ReservationSerializer(serializers.ModelSerializer):
    capsule_name = serializers.CharField(source="capsule.name", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "capsule",
            "capsule_name",
            "visitor_name",
            "starts_at",
            "pickup_deadline",
            "status",
            "checked_out_at",
            "returned_at",
            "return_notes",
            "created_at",
        ]
        read_only_fields = ["status", "checked_out_at", "returned_at", "created_at"]

    def validate(self, attrs):
        capsule = attrs.get("capsule")
        if not capsule:
            return attrs

        if capsule.expires_at < timezone.localdate():
            raise serializers.ValidationError("Cápsula vencida não pode ser reservada.")

        return attrs

    def create(self, validated_data):
        capsule_id = validated_data["capsule"].id

        with transaction.atomic():
            capsule = Capsule.objects.select_for_update().get(pk=capsule_id)

            if capsule.status != Capsule.Status.AVAILABLE:
                raise serializers.ValidationError("Cápsula não está disponível para reserva.")

            if Reservation.objects.filter(
                capsule=capsule, status=Reservation.Status.PENDING
            ).exists():
                raise serializers.ValidationError("Cápsula já possui uma reserva pendente.")

            validated_data["capsule"] = capsule
            reservation = Reservation.objects.create(**validated_data)
            actor = describe_actor(
                self.context.get("request"),
                fallback=f"visitante: {reservation.visitor_name}",
            )
            record_status_change(
                reservation.capsule,
                Capsule.Status.RESERVED,
                actor=actor,
                reason=f"reserva criada para {reservation.visitor_name}",
            )

        return reservation


class ReturnReservationSerializer(serializers.Serializer):
    damaged = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class QualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = ["id", "capsule", "reservation", "inspector_name", "result", "notes", "created_at"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        check = QualityCheck.objects.create(**validated_data)
        if check.result in {QualityCheck.Result.FAILED, QualityCheck.Result.DAMAGED}:
            record_status_change(
                check.capsule,
                Capsule.Status.QUARANTINE,
                actor=describe_actor(self.context.get("request")),
                reason=f"inspeção reprovada ({check.get_result_display()})",
            )
        return check


class ExternalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalEvent
        fields = ["id", "event_id", "source", "event_type", "payload", "processed_at", "created_at"]
        read_only_fields = ["processed_at", "created_at"]
        validators = []


class MuseumProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuseumProfile
        fields = ["id", "user", "role", "display_name", "created_at"]
        read_only_fields = ["created_at"]


class StatusChangeSerializer(serializers.ModelSerializer):
    capsule_name = serializers.CharField(source="capsule.name", read_only=True)

    class Meta:
        model = StatusChange
        fields = [
            "id",
            "capsule",
            "capsule_name",
            "from_status",
            "to_status",
            "actor",
            "reason",
            "created_at",
        ]
        read_only_fields = ["created_at"]
