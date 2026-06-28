# Generated for the challenge repository.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Batch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=32, unique=True)),
                ("preservation_method", models.CharField(max_length=80)),
                ("produced_at", models.DateField()),
                ("expires_at", models.DateField()),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="ExternalEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("event_id", models.CharField(max_length=80)),
                ("source", models.CharField(max_length=80)),
                ("event_type", models.CharField(max_length=80)),
                ("payload", models.JSONField(default=dict)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Capsule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("scent_profile", models.CharField(max_length=180)),
                ("origin_story", models.TextField(blank=True)),
                ("intensity", models.PositiveSmallIntegerField(default=3)),
                (
                    "rarity",
                    models.CharField(
                        choices=[("common", "Comum"), ("rare", "Rara"), ("unique", "Única")],
                        default="common",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("available", "Disponível"),
                            ("reserved", "Reservada"),
                            ("checked_out", "Retirada"),
                            ("quarantine", "Quarentena"),
                            ("retired", "Aposentada"),
                        ],
                        default="available",
                        max_length=16,
                    ),
                ),
                ("expires_at", models.DateField()),
                ("requires_manual_approval", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="capsules",
                        to="scents.batch",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("visitor_name", models.CharField(max_length=120)),
                ("starts_at", models.DateTimeField()),
                ("pickup_deadline", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("checked_out", "Retirada"),
                            ("returned", "Devolvida"),
                            ("expired", "Expirada"),
                            ("cancelled", "Cancelada"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("checked_out_at", models.DateTimeField(blank=True, null=True)),
                ("returned_at", models.DateTimeField(blank=True, null=True)),
                ("return_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "capsule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="scents.capsule",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="QualityCheck",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("inspector_name", models.CharField(max_length=120)),
                (
                    "result",
                    models.CharField(
                        choices=[
                            ("passed", "Aprovada"),
                            ("failed", "Reprovada"),
                            ("damaged", "Danificada"),
                        ],
                        max_length=16,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "capsule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quality_checks",
                        to="scents.capsule",
                    ),
                ),
                (
                    "reservation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="quality_checks",
                        to="scents.reservation",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
