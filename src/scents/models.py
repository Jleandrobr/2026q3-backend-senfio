import logging

from django.conf import settings
from django.db import models, transaction

logger = logging.getLogger(__name__)


class MuseumProfile(models.Model):
    """Perfil operacional de um usuário do museu.

    Define o papel que governa o que a pessoa pode fazer na API: curadoria,
    inspeção técnica ou visitação.
    """

    class Role(models.TextChoices):
        CURATOR = "curator", "Curador"
        TECHNICIAN = "technician", "Técnico"
        VISITOR = "visitor", "Visitante"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="museum_profile",
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.VISITOR)
    display_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_role_display()})"


class Batch(models.Model):
    code = models.CharField(max_length=32, unique=True)
    preservation_method = models.CharField(max_length=80)
    produced_at = models.DateField()
    expires_at = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.code


class Capsule(models.Model):
    class Rarity(models.TextChoices):
        COMMON = "common", "Comum"
        RARE = "rare", "Rara"
        UNIQUE = "unique", "Única"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponível"
        RESERVED = "reserved", "Reservada"
        CHECKED_OUT = "checked_out", "Retirada"
        QUARANTINE = "quarantine", "Quarentena"
        RETIRED = "retired", "Aposentada"

    batch = models.ForeignKey(Batch, related_name="capsules", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    scent_profile = models.CharField(max_length=180)
    origin_story = models.TextField(blank=True)
    intensity = models.PositiveSmallIntegerField(default=3)
    rarity = models.CharField(max_length=16, choices=Rarity.choices, default=Rarity.COMMON)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    expires_at = models.DateField()
    requires_manual_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding and self.rarity in {self.Rarity.RARE, self.Rarity.UNIQUE}:
            self.requires_manual_approval = True
        super().save(*args, **kwargs)


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        CHECKED_OUT = "checked_out", "Retirada"
        RETURNED = "returned", "Devolvida"
        EXPIRED = "expired", "Expirada"
        CANCELLED = "cancelled", "Cancelada"

    capsule = models.ForeignKey(Capsule, related_name="reservations", on_delete=models.PROTECT)
    visitor_name = models.CharField(max_length=120)
    starts_at = models.DateTimeField()
    pickup_deadline = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.visitor_name} -> {self.capsule}"


class QualityCheck(models.Model):
    class Result(models.TextChoices):
        PASSED = "passed", "Aprovada"
        FAILED = "failed", "Reprovada"
        DAMAGED = "damaged", "Danificada"

    capsule = models.ForeignKey(Capsule, related_name="quality_checks", on_delete=models.PROTECT)
    reservation = models.ForeignKey(
        Reservation,
        related_name="quality_checks",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    inspector_name = models.CharField(max_length=120)
    result = models.CharField(max_length=16, choices=Result.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ExternalEvent(models.Model):
    event_id = models.CharField(max_length=80)
    source = models.CharField(max_length=80)
    event_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "event_id"], name="unique_external_event"),
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.event_id}"


class StatusChange(models.Model):
    """Trilha de auditoria das transições de status de uma cápsula.

    Cada registro guarda de onde para onde a cápsula mudou, quem provocou a
    mudança e por quê. A trilha é histórica: serve para reconstruir a vida de
    uma cápsula no acervo.
    """

    capsule = models.ForeignKey(
        Capsule,
        related_name="status_changes",
        on_delete=models.PROTECT,
    )
    from_status = models.CharField(max_length=16, choices=Capsule.Status.choices)
    to_status = models.CharField(max_length=16, choices=Capsule.Status.choices)
    actor = models.CharField(max_length=120, blank=True)
    reason = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.capsule}: {self.from_status} -> {self.to_status}"


def describe_actor(request, fallback=""):
    """Descreve quem fez a requisição, a partir do MuseumProfile autenticado (BR-007).

    Sem perfil autenticado (ex.: visitante anônimo criando uma reserva), usa
    `fallback` — nunca deixa em branco silenciosamente.
    """
    profile = getattr(getattr(request, "user", None), "museum_profile", None)
    if profile is None:
        return fallback
    return f"{profile.display_name} ({profile.get_role_display()})"


def notify_quarantine(capsule, reason=""):
    logger.warning(
        "ALERTA CURADORIA: cápsula '%s' entrou em quarentena (%s)",
        capsule.name,
        reason or "sem motivo informado",
    )


def record_status_change(capsule, to_status, actor="", reason=""):
    """Registra uma transição de status na trilha de auditoria.

    Move a cápsula para `to_status` e cria o `StatusChange` correspondente.
    """
    with transaction.atomic():
        from_status = capsule.status
        StatusChange.objects.create(
            capsule=capsule,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            reason=reason,
        )
        capsule.status = to_status
        capsule.save(update_fields=["status", "updated_at"])

    if to_status == Capsule.Status.QUARANTINE:
        notify_quarantine(capsule, reason=reason)


def expire_reservation(reservation, reason="", actor="sistema"):
    """Expira uma reserva pendente vencida e libera a cápsula (BR-006).

    Compartilhado pelo comando recorrente de expiração e pelo checkout
    tardio de uma reserva já vencida, para que as duas trilhas de auditoria
    fiquem idênticas.
    """
    with transaction.atomic():
        reservation.status = Reservation.Status.EXPIRED
        reservation.save(update_fields=["status"])
        record_status_change(
            reservation.capsule, Capsule.Status.AVAILABLE, actor=actor, reason=reason
        )
