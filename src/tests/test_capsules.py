from datetime import timedelta

from django.utils import timezone


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
    assert response.data[0]["batch_code"] == capsule.batch.code
