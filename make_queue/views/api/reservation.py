from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone

from make_queue.models.models import Reservation, Quota, ReservationRule


def get_machine_data(request, machine, reservation=None):
    return JsonResponse({
        "reservations": [{"start_date": c_reservation.start_time, "end_date": c_reservation.end_time} for c_reservation in
                         Reservation.objects.filter(end_time__gte=timezone.now()) if c_reservation != reservation],
        "canIgnoreRules": any(quota.ignore_rules and quota.can_make_more_reservations(request.user) for quota in
                               Quota.get_user_quotas(request.user, machine.machine_type)),
        "rules": [
            {
                "periods": [
                    [
                        day + rule.start_time.hour / 24 + rule.start_time.minute / 1440,
                        (day + rule.days_changed + rule.end_time.hour / 24 + rule.end_time.minute / 1440) % 7
                    ]
                    for day, _ in enumerate(bin(rule.start_days)[2:][::-1]) if _ == "1"
                ],
                "max_hours": rule.max_hours,
                "max_hours_crossed": rule.max_inside_border_crossed,
            } for rule in ReservationRule.objects.filter(machine_type=machine.machine_type)]
    })


def get_reservations_day_and_machine(request, machine, date):
    reservations = machine.get_reservation_set().filter(start_time__lt=date + timedelta(days=1)).filter(
        end_time__gte=date)

    return JsonResponse({"reservations": reservations, "date": date})


def get_future_reservations_machine_without_specific_reservation(request, reservation):
    reservations = reservation.machine.get_reservation_set().filter(end_time__gte=timezone.now()).exclude(
        pk=reservation.pk)

    return JsonResponse(format_reservations_for_start_end_json(reservations))


def format_reservations_for_start_end_json(reservations):
    return {"reservations": [{"start_date": reservation.start_time, "end_date": reservation.end_time} for reservation in
                             reservations]}
