from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from scents.models import Batch, Capsule


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def batch(db):
    today = timezone.localdate()
    return Batch.objects.create(
        code="TEST-001",
        preservation_method="vidro âmbar pressurizado",
        produced_at=today - timedelta(days=1),
        expires_at=today + timedelta(days=90),
    )


@pytest.fixture
def capsule(batch):
    return Capsule.objects.create(
        batch=batch,
        name="Feira depois da chuva",
        scent_profile="coentro, lona molhada e fruta madura",
        expires_at=timezone.localdate() + timedelta(days=60),
    )
