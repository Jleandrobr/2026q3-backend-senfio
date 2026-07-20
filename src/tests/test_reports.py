from datetime import timedelta

from django.utils import timezone

from scents.models import Capsule


def test_occupancy_report_counts_capsules_by_status(api_client, batch):
    Capsule.objects.create(
        batch=batch,
        name="Disponível 1",
        scent_profile="teste",
        status=Capsule.Status.AVAILABLE,
        expires_at=timezone.localdate() + timedelta(days=30),
    )
    Capsule.objects.create(
        batch=batch,
        name="Disponível 2",
        scent_profile="teste",
        status=Capsule.Status.AVAILABLE,
        expires_at=timezone.localdate() + timedelta(days=30),
    )
    Capsule.objects.create(
        batch=batch,
        name="Em quarentena",
        scent_profile="teste",
        status=Capsule.Status.QUARANTINE,
        expires_at=timezone.localdate() + timedelta(days=30),
    )

    response = api_client.get("/api/reports/occupancy/")

    assert response.status_code == 200
    assert response.data["available"] == 2
    assert response.data["quarantine"] == 1
    assert response.data["reserved"] == 0
    assert response.data["checked_out"] == 0
    assert response.data["retired"] == 0


def test_occupancy_report_includes_all_statuses_for_empty_collection(api_client, db):
    response = api_client.get("/api/reports/occupancy/")

    assert response.status_code == 200
    assert response.data == {
        "available": 0,
        "reserved": 0,
        "checked_out": 0,
        "quarantine": 0,
        "retired": 0,
    }
