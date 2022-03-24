from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ...models.machine import Machine
from ...models.reservation import Quota


def get_machine_data(request, pk: int, reservation_pk: int = None):
    machine = get_object_or_404(Machine, pk=pk)
    reservation = get_object_or_404(machine.reservations, pk=reservation_pk) if reservation_pk is not None else None
    return JsonResponse({
        "reservations": [
            {"start_time": c_reservation.start_time, "end_time": c_reservation.end_time}
            for c_reservation in machine.reservations.filter(end_time__gte=timezone.now())
            if c_reservation != reservation
        ],
        "canIgnoreRules": any(quota.ignore_rules and quota.can_create_more_reservations(request.user) for quota in
                              Quota.get_user_quotas(request.user, machine.machine_type)),
        "rules": [
            {
                "periods": [
                    [
                        day + rule.start_time.hour / 24 + rule.start_time.minute / (24 * 60),
                        (day + rule.days_changed + rule.end_time.hour / 24 + rule.end_time.minute / (24 * 60)) % 7
                    ]
                    for day in rule.get_start_day_indices(iso=False)
                ],
                "max_hours": rule.max_hours,
                "max_hours_crossed": rule.max_inside_border_crossed,
            } for rule in machine.machine_type.reservation_rules.all()],
    })
