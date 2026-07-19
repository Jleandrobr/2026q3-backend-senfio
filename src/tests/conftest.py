from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from scents.models import Batch, Capsule, MuseumProfile


@pytest.fixture
def api_client():
    return APIClient()


def _authenticated_client(role, username):
    user = get_user_model().objects.create_user(username=username)
    MuseumProfile.objects.create(user=user, display_name=username, role=role)
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def curator_client(db):
    return _authenticated_client(MuseumProfile.Role.CURATOR, "curador-teste")


@pytest.fixture
def technician_client(db):
    return _authenticated_client(MuseumProfile.Role.TECHNICIAN, "tecnico-teste")


@pytest.fixture
def visitor_client(db):
    return _authenticated_client(MuseumProfile.Role.VISITOR, "visitante-teste")


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
