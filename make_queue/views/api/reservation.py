from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone


def get_future_reservations_machine(request, machine):
    reservations = machine.get_reservation_set().filter(end_time__gte=timezone.now())
    return JsonResponse(format_reservations_for_start_end_json(reservations))


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
