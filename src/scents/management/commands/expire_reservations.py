from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from scents.models import Reservation, expire_reservation


class Command(BaseCommand):
    help = (
        "Varre reservas pendentes cujo prazo de retirada venceu, expira-as e "
        "libera a cápsula (BR-006). Pensado para rodar periodicamente (cron)."
    )

    def handle(self, *args, **options):
        overdue_ids = Reservation.objects.filter(
            status=Reservation.Status.PENDING,
            pickup_deadline__lt=timezone.now(),
        ).values_list("id", flat=True)

        expired_count = 0
        for reservation_id in overdue_ids:
            with transaction.atomic():
                reservation = (
                    Reservation.objects.select_for_update()
                    .select_related("capsule")
                    .get(pk=reservation_id)
                )
                if (
                    reservation.status != Reservation.Status.PENDING
                    or reservation.pickup_deadline >= timezone.now()
                ):
                    continue

                expire_reservation(
                    reservation, reason="expiração automática (prazo de retirada vencido)"
                )
                expired_count += 1

        self.stdout.write(self.style.SUCCESS(f"{expired_count} reserva(s) expirada(s)."))
