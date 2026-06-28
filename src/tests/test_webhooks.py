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
