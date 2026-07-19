from datetime import timedelta

from django.utils import timezone


def test_create_capsule_without_profile_is_rejected(api_client, batch):
    response = api_client.post(
        "/api/capsules/",
        {
            "batch": batch.id,
            "name": "Cápsula sem permissão",
            "scent_profile": "teste",
            "expires_at": str(timezone.localdate() + timedelta(days=30)),
        },
        format="json",
    )

    assert response.status_code == 403


def test_technician_cannot_retire_capsule(technician_client, capsule):
    response = technician_client.patch(
        f"/api/capsules/{capsule.id}/",
        {"status": "retired"},
        format="json",
    )

    assert response.status_code == 403


def test_curator_can_retire_capsule(curator_client, capsule):
    response = curator_client.patch(
        f"/api/capsules/{capsule.id}/",
        {"status": "retired"},
        format="json",
    )

    assert response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.status == "retired"


def test_capsules_are_readable_without_authentication(api_client, capsule):
    response = api_client.get("/api/capsules/")

    assert response.status_code == 200


def test_visitor_cannot_register_quality_check(visitor_client, capsule):
    response = visitor_client.post(
        "/api/quality-checks/",
        {"capsule": capsule.id, "inspector_name": "Vera", "result": "passed"},
        format="json",
    )

    assert response.status_code == 403


def test_technician_can_register_quality_check(technician_client, capsule):
    response = technician_client.post(
        "/api/quality-checks/",
        {"capsule": capsule.id, "inspector_name": "Tito", "result": "passed"},
        format="json",
    )

    assert response.status_code == 201


def test_visitor_can_create_reservation(visitor_client, capsule):
    response = visitor_client.post(
        "/api/reservations/",
        {
            "capsule": capsule.id,
            "visitor_name": "Vera",
            "starts_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "pickup_deadline": (timezone.now() + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 201


def test_technician_cannot_manage_profiles(technician_client):
    response = technician_client.post(
        "/api/profiles/",
        {"display_name": "X", "role": "curator"},
        format="json",
    )

    assert response.status_code == 403


def test_curator_can_manage_profiles(curator_client, django_user_model):
    another_user = django_user_model.objects.create_user(username="novo-perfil")

    response = curator_client.post(
        "/api/profiles/",
        {"user": another_user.id, "display_name": "Novo Perfil", "role": "visitor"},
        format="json",
    )

    assert response.status_code == 201
