from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from ...models.models import Machine


def reservation_type(reservation, user):
    if reservation.special:
        return "make"
    if reservation.event:
        return "event"
    if user is not None and reservation.user == user:
        return "own"
    return "normal"


def get_reservations(request, machine: Machine):
    start_date = parse_datetime(request.GET.get("startDate"))
    end_date = parse_datetime(request.GET.get("endDate"))

    reservations = []
    for reservation in machine.reservations.filter(start_time__lt=end_date, end_time__gt=start_date):
        reservation_data = {
            "start": reservation.start_time,
            "end": reservation.end_time,
            "type": reservation_type(reservation, request.user),
        }

        if reservation.event:
            reservation_data.update({
                "eventLink": reverse("event", kwargs={"pk": reservation.event.event.pk}),
                "displayText": str(reservation.event.event.title),
            })
        elif reservation.special:
            reservation_data.update({
                "displayText": reservation.special_text,
            })
        elif request.user.has_perm("make_queue.can_view_reservation_user"):
            reservation_data.update({
                "user": reservation.user.get_full_name(),
                "email": reservation.user.email,
                "displayText": reservation.comment,
            })

        reservations.append(reservation_data)

    return JsonResponse({"reservations": reservations})


def get_reservation_rules(request, machine):
    return JsonResponse({
        "rules": [
            {
                "periods": [
                    [
                        day + rule.start_time.hour / 24 + rule.start_time.minute / (24 * 60),
                        (day + rule.days_changed + rule.end_time.hour / 24 + rule.end_time.minute / (24 * 60)) % 7
                    ]
                    for day, _ in enumerate(bin(rule.start_days)[2:][::-1]) if _ == "1"
                ],
                "max_inside": rule.max_hours,
                "max_crossed": rule.max_inside_border_crossed,
            } for rule in machine.machine_type.reservation_rules.all()
        ],
    })
