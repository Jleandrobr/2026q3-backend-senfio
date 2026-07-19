from scents.models import Capsule, ExternalEvent, StatusChange


def test_external_webhook_records_event(api_client, capsule):
    response = api_client.post(
        "/api/webhooks/external-museum/",
        {
            "event_id": "evt-001",
            "source": "museu-parceiro",
            "event_type": "capsule.quarantined",
            "payload": {"capsule_id": capsule.id},
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["event_id"] == "evt-001"


def test_external_webhook_quarantines_capsule_with_audit_trail(api_client, capsule):
    response = api_client.post(
        "/api/webhooks/external-museum/",
        {
            "event_id": "evt-002",
            "source": "museu-parceiro",
            "event_type": "capsule.quarantined",
            "payload": {"capsule_id": capsule.id},
        },
        format="json",
    )

    assert response.status_code == 201
    capsule.refresh_from_db()
    assert capsule.status == Capsule.Status.QUARANTINE
    assert StatusChange.objects.filter(
        capsule=capsule, to_status=Capsule.Status.QUARANTINE
    ).exists()


def test_external_webhook_is_idempotent_by_source_and_event_id(api_client, capsule):
    payload = {
        "event_id": "evt-003",
        "source": "museu-parceiro",
        "event_type": "capsule.quarantined",
        "payload": {"capsule_id": capsule.id},
    }

    first = api_client.post("/api/webhooks/external-museum/", payload, format="json")
    second = api_client.post("/api/webhooks/external-museum/", payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 200
    assert ExternalEvent.objects.filter(source="museu-parceiro", event_id="evt-003").count() == 1
    assert (
        StatusChange.objects.filter(capsule=capsule, to_status=Capsule.Status.QUARANTINE).count()
        == 1
    )


def test_external_webhook_rejects_unknown_capsule_id(api_client, db):
    response = api_client.post(
        "/api/webhooks/external-museum/",
        {
            "event_id": "evt-004",
            "source": "museu-parceiro",
            "event_type": "capsule.quarantined",
            "payload": {"capsule_id": 999999},
        },
        format="json",
    )

    assert response.status_code == 400
    assert not ExternalEvent.objects.filter(event_id="evt-004").exists()
