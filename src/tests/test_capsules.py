from datetime import timedelta

from django.utils import timezone

from scents.models import Capsule, QualityCheck, StatusChange


def test_create_capsule(curator_client, batch):
    response = curator_client.post(
        "/api/capsules/",
        {
            "batch": batch.id,
            "name": "Padaria com ficha de pão",
            "scent_profile": "fermento, moeda antiga e balcão de fórmica",
            "origin_story": "Coletada por memória oral.",
            "intensity": 4,
            "rarity": "common",
            "status": "available",
            "expires_at": str(timezone.localdate() + timedelta(days=30)),
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["name"] == "Padaria com ficha de pão"


def test_list_capsules_includes_batch_code(api_client, capsule):
    response = api_client.get("/api/capsules/")

    assert response.status_code == 200
    assert response.data["results"][0]["batch_code"] == capsule.batch.code


def test_list_capsules_is_paginated(api_client, capsule):
    response = api_client.get("/api/capsules/")

    assert response.status_code == 200
    assert set(response.data.keys()) == {"count", "next", "previous", "results"}
    assert response.data["count"] == 1


def test_list_capsules_accepts_ordering(api_client, capsule, batch):
    Capsule.objects.create(
        batch=batch,
        name="Zimbro Molhado na Estufa",
        scent_profile="teste",
        expires_at=timezone.localdate() + timedelta(days=60),
    )

    response = api_client.get("/api/capsules/", {"ordering": "-name"})

    assert response.status_code == 200
    names = [item["name"] for item in response.data["results"]]
    assert names == sorted(names, reverse=True)
    assert names[0] == "Zimbro Molhado na Estufa"


def test_list_capsules_filters_by_status(api_client, capsule):
    capsule.status = "quarantine"
    capsule.save(update_fields=["status"])

    response = api_client.get("/api/capsules/", {"status": "quarantine"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [capsule.id]

    response = api_client.get("/api/capsules/", {"status": "available"})

    assert response.status_code == 200
    assert capsule.id not in [item["id"] for item in response.data["results"]]


def test_list_capsules_filters_by_rarity(api_client, capsule):
    capsule.rarity = "unique"
    capsule.save(update_fields=["rarity"])

    response = api_client.get("/api/capsules/", {"rarity": "unique"})

    assert response.status_code == 200
    assert [item["id"] for item in response.data["results"]] == [capsule.id]

    response = api_client.get("/api/capsules/", {"rarity": "common"})

    assert response.status_code == 200
    assert capsule.id not in [item["id"] for item in response.data["results"]]


def test_quality_check_failure_quarantines_capsule_with_audit_trail(technician_client, capsule):
    response = technician_client.post(
        "/api/quality-checks/",
        {
            "capsule": capsule.id,
            "inspector_name": "Ana",
            "result": QualityCheck.Result.FAILED,
            "notes": "cheiro alterado na inspeção de rotina",
        },
        format="json",
    )

    assert response.status_code == 201
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.QUARANTINE
    assert StatusChange.objects.filter(
        capsule=capsule, to_status=Capsule.Status.QUARANTINE
    ).exists()


def test_capsule_timeline_is_empty_for_capsule_without_changes(api_client, capsule):
    response = api_client.get(f"/api/capsules/{capsule.id}/timeline/")

    assert response.status_code == 200
    assert response.data == []


def test_curator_retires_capsule_with_audit_trail(curator_client, capsule):
    response = curator_client.post(f"/api/capsules/{capsule.id}/retire/")

    assert response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.RETIRED
    assert StatusChange.objects.filter(capsule=capsule, to_status=Capsule.Status.RETIRED).exists()


def test_retiring_already_retired_capsule_is_rejected(curator_client, capsule):
    capsule.status = Capsule.Status.RETIRED
    capsule.save(update_fields=["status"])

    response = curator_client.post(f"/api/capsules/{capsule.id}/retire/")

    assert response.status_code == 400


def test_non_curator_cannot_retire_capsule(api_client, capsule):
    response = api_client.post(f"/api/capsules/{capsule.id}/retire/")

    assert response.status_code == 403
    capsule.refresh_from_db()
    assert capsule.status != Capsule.Status.RETIRED


def test_capsule_timeline_lists_status_changes_in_chronological_order(api_client, capsule):
    reservation_response = api_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Bruno",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )
    reservation_id = reservation_response.data["id"]
    api_client.post(f"/api/reservations/{reservation_id}/checkout/")

    response = api_client.get(f"/api/capsules/{capsule.id}/timeline/")

    assert response.status_code == 200
    to_statuses = [item["to_status"] for item in response.data]
    assert to_statuses == ["reserved", "checked_out"]
    created_ats = [item["created_at"] for item in response.data]
    assert created_ats == sorted(created_ats)


def test_rare_capsule_always_requires_manual_approval(curator_client, batch):
    response = curator_client.post(
        "/api/capsules/",
        {
            "batch": batch.id,
            "name": "Cápsula rara sem flag explícita",
            "scent_profile": "teste",
            "rarity": "rare",
            "requires_manual_approval": False,
            "expires_at": str(timezone.localdate() + timedelta(days=30)),
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["requires_manual_approval"] is True
