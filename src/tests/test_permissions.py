from datetime import timedelta

from django.utils import timezone

from scents.models import Reservation, record_status_change


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


def test_technician_cannot_approve_capsule(technician_client, capsule):
    capsule.requires_manual_approval = True
    capsule.save(update_fields=["requires_manual_approval"])

    response = technician_client.post(f"/api/capsules/{capsule.id}/approve/")

    assert response.status_code == 403


def test_curator_can_approve_capsule(curator_client, capsule):
    capsule.requires_manual_approval = True
    capsule.save(update_fields=["requires_manual_approval"])

    response = curator_client.post(f"/api/capsules/{capsule.id}/approve/")

    assert response.status_code == 200
    capsule.refresh_from_db()
    assert capsule.requires_manual_approval is False


def test_curator_can_manage_profiles(curator_client, django_user_model):
    another_user = django_user_model.objects.create_user(username="novo-perfil")

    response = curator_client.post(
        "/api/profiles/",
        {"user": another_user.id, "display_name": "Novo Perfil", "role": "visitor"},
        format="json",
    )

    assert response.status_code == 201


def test_status_changes_cannot_be_created_via_api(curator_client, capsule):
    response = curator_client.post(
        "/api/status-changes/",
        {
            "capsule": capsule.id,
            "from_status": "available",
            "to_status": "retired",
            "actor": "forjado",
            "reason": "forjado",
        },
        format="json",
    )

    assert response.status_code == 405


def test_status_changes_cannot_be_edited_or_deleted_via_api(curator_client, capsule):
    record_status_change(capsule, "retired", reason="aposentada pela curadoria")
    change = capsule.status_changes.get()

    patch_response = curator_client.patch(
        f"/api/status-changes/{change.id}/", {"reason": "editado"}, format="json"
    )
    delete_response = curator_client.delete(f"/api/status-changes/{change.id}/")

    assert patch_response.status_code == 405
    assert delete_response.status_code == 405


def test_reservations_cannot_be_updated_or_deleted_via_api(api_client, capsule):
    reservation = Reservation.objects.create(
        capsule=capsule,
        visitor_name="Bruno",
        starts_at=timezone.now() + timedelta(days=1),
        pickup_deadline=timezone.now() + timedelta(days=1, hours=2),
    )

    patch_response = api_client.patch(
        f"/api/reservations/{reservation.id}/",
        {"pickup_deadline": (timezone.now() + timedelta(days=365)).isoformat()},
        format="json",
    )
    delete_response = api_client.delete(f"/api/reservations/{reservation.id}/")

    assert patch_response.status_code == 405
    assert delete_response.status_code == 405
