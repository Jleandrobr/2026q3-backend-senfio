import threading
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from scents.models import Capsule, QualityCheck, Reservation, StatusChange


def test_reservation_rejects_expired_capsule(api_client, capsule):
    capsule.expires_at = timezone.localdate() - timedelta(days=1)
    capsule.save(update_fields=["expires_at"])

    response = api_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Ana",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 400


def test_reservation_rejects_quarantined_capsule(api_client, capsule):
    capsule.status = Capsule.Status.QUARANTINE
    capsule.save(update_fields=["status"])

    response = api_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Ana",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 400


def test_reservation_rejected_when_capsule_already_has_active_reservation(api_client, capsule):
    payload = {
        "capsule": capsule.id,
        "visitor_name": "Primeira",
        "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
        "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
    }
    first_response = api_client.post("/api/reservations/", payload, format="json")
    assert first_response.status_code == 201

    second_response = api_client.post(
        "/api/reservations/", {**payload, "visitor_name": "Segunda"}, format="json"
    )

    assert second_response.status_code == 400
    assert Reservation.objects.filter(capsule=capsule).count() == 1


def test_valid_reservation_moves_capsule_to_reserved(api_client, capsule):
    response = api_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Ana",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 201
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.RESERVED


def test_checkout_marks_capsule_as_checked_out(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() + timedelta(days=1),
        pickup_deadline=timezone.now() + timedelta(days=1, hours=2),
    )

    response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.CHECKED_OUT


def test_checkout_rejected_when_reservation_not_pending(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        status=Reservation.Status.CHECKED_OUT,
        starts_at=timezone.now() - timedelta(hours=1),
        pickup_deadline=timezone.now() + timedelta(hours=1),
        checked_out_at=timezone.now() - timedelta(hours=1),
    )

    response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert response.status_code == 400


def test_checkout_creates_audit_trail(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() + timedelta(days=1),
        pickup_deadline=timezone.now() + timedelta(days=1, hours=2),
    )

    response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert response.status_code == 200
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.CHECKED_OUT)
    assert change.actor == "visitante: Bruno"


def test_reservation_create_records_anonymous_visitor_as_actor(api_client, capsule):
    response = api_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Ana",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 201
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.RESERVED)
    assert change.actor == "visitante: Ana"


def test_reservation_create_records_authenticated_profile_as_actor(curator_client, capsule):
    response = curator_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Ana",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 201
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.RESERVED)
    assert change.actor == "curador-teste (Curador)"


def test_checkout_after_deadline_expires_reservation_with_audit_trail(api_client, capsule):
    capsule.status = Capsule.Status.RESERVED
    capsule.save(update_fields=["status"])
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() - timedelta(days=2),
        pickup_deadline=timezone.now() - timedelta(days=1),
    )

    response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert response.status_code == 400
    reservation.refresh_from_db()
    capsule.refresh_from_db()
    assert reservation.status == Reservation.Status.EXPIRED
    assert capsule.status == Capsule.Status.AVAILABLE
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.AVAILABLE)
    assert change.actor == "sistema"


def test_expire_reservations_command_expires_overdue_pending(capsule):
    capsule.status = Capsule.Status.RESERVED
    capsule.save(update_fields=["status"])
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Carla",
        starts_at=timezone.now() - timedelta(days=2),
        pickup_deadline=timezone.now() - timedelta(hours=1),
    )

    call_command("expire_reservations")

    reservation.refresh_from_db()
    capsule.refresh_from_db()
    assert reservation.status == Reservation.Status.EXPIRED
    assert capsule.status == Capsule.Status.AVAILABLE
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.AVAILABLE)
    assert change.actor == "sistema"


def test_expire_reservations_command_ignores_pending_within_deadline(capsule):
    capsule.status = Capsule.Status.RESERVED
    capsule.save(update_fields=["status"])
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Diego",
        starts_at=timezone.now() + timedelta(hours=1),
        pickup_deadline=timezone.now() + timedelta(hours=2),
    )

    call_command("expire_reservations")

    reservation.refresh_from_db()
    capsule.refresh_from_db()
    assert reservation.status == Reservation.Status.PENDING
    assert capsule.status == Capsule.Status.RESERVED


def test_checkout_blocked_when_capsule_requires_approval(api_client, capsule):
    capsule.requires_manual_approval = True
    capsule.save(update_fields=["requires_manual_approval"])
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() + timedelta(days=1),
        pickup_deadline=timezone.now() + timedelta(days=1, hours=2),
    )

    response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert response.status_code == 400
    capsule.refresh_from_db()
    assert capsule.status != Capsule.Status.CHECKED_OUT


def test_checkout_succeeds_after_curator_approval(api_client, curator_client, capsule):
    capsule.requires_manual_approval = True
    capsule.save(update_fields=["requires_manual_approval"])
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() + timedelta(days=1),
        pickup_deadline=timezone.now() + timedelta(days=1, hours=2),
    )

    approve_response = curator_client.post(f"/api/capsules/{capsule.id}/approve/")
    assert approve_response.status_code == 200

    checkout_response = api_client.post(f"/api/reservations/{reservation.id}/checkout/")

    assert checkout_response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.CHECKED_OUT


def test_return_without_damage_records_actor(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        status=Reservation.Status.CHECKED_OUT,
        starts_at=timezone.now() - timedelta(hours=1),
        pickup_deadline=timezone.now() + timedelta(hours=1),
        checked_out_at=timezone.now() - timedelta(hours=1),
    )
    capsule.status = Capsule.Status.CHECKED_OUT
    capsule.save(update_fields=["status"])

    response = api_client.post(f"/api/reservations/{reservation.id}/return/")

    assert response.status_code == 200
    reservation.refresh_from_db()
    capsule.refresh_from_db()
    assert reservation.status == Reservation.Status.RETURNED
    assert capsule.status == Capsule.Status.AVAILABLE
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.AVAILABLE)
    assert change.actor == "visitante: Bruno"


def test_return_with_damage_records_actor(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        status=Reservation.Status.CHECKED_OUT,
        starts_at=timezone.now() - timedelta(hours=1),
        pickup_deadline=timezone.now() + timedelta(hours=1),
        checked_out_at=timezone.now() - timedelta(hours=1),
    )
    capsule.status = Capsule.Status.CHECKED_OUT
    capsule.save(update_fields=["status"])

    response = api_client.post(
        f"/api/reservations/{reservation.id}/return/", {"damaged": True}, format="json"
    )

    assert response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.QUARANTINE
    change = StatusChange.objects.get(capsule=capsule, to_status=Capsule.Status.QUARANTINE)
    assert change.actor == "visitante: Bruno"
    assert QualityCheck.objects.filter(
        reservation=reservation, result=QualityCheck.Result.DAMAGED
    ).exists()


def test_return_with_damage_is_atomic_if_quality_check_creation_fails(
    api_client, capsule, monkeypatch
):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        status=Reservation.Status.CHECKED_OUT,
        starts_at=timezone.now() - timedelta(hours=1),
        pickup_deadline=timezone.now() + timedelta(hours=1),
        checked_out_at=timezone.now() - timedelta(hours=1),
    )
    capsule.status = Capsule.Status.CHECKED_OUT
    capsule.save(update_fields=["status"])

    def boom(*args, **kwargs):
        raise RuntimeError("falha simulada na criação da inspeção")

    monkeypatch.setattr("scents.views.QualityCheck.objects.create", boom)

    with pytest.raises(RuntimeError):
        api_client.post(
            f"/api/reservations/{reservation.id}/return/", {"damaged": True}, format="json"
        )

    reservation.refresh_from_db()
    capsule.refresh_from_db()
    assert reservation.status == Reservation.Status.CHECKED_OUT
    assert capsule.status == Capsule.Status.CHECKED_OUT
    assert not StatusChange.objects.filter(
        capsule=capsule, to_status=Capsule.Status.QUARANTINE
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_reservations_only_one_succeeds(batch):
    capsule = Capsule.objects.create(
        batch=batch,
        name="Concorrência à Prova de Bala",
        scent_profile="ozônio sob pressão",
        expires_at=timezone.localdate() + timedelta(days=60),
    )

    payload = {
        "capsule": capsule.id,
        "visitor_name": "Concorrente",
        "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
        "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
    }
    status_codes = []

    def reserve():
        try:
            response = APIClient().post("/api/reservations/", payload, format="json")
            status_codes.append(response.status_code)
        finally:
            connection.close()

    threads = [threading.Thread(target=reserve) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert status_codes.count(201) == 1
    assert status_codes.count(400) == 9
    assert Reservation.objects.filter(capsule=capsule).count() == 1
