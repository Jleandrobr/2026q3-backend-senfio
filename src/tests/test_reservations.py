import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from scents.models import Capsule, Reservation


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
