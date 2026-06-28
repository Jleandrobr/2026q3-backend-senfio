from django.contrib import admin

from scents.models import (
    Batch,
    Capsule,
    ExternalEvent,
    MuseumProfile,
    QualityCheck,
    Reservation,
    StatusChange,
)

admin.site.register(Batch)
admin.site.register(Capsule)
admin.site.register(Reservation)
admin.site.register(QualityCheck)
admin.site.register(ExternalEvent)
admin.site.register(MuseumProfile)
admin.site.register(StatusChange)
