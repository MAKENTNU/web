from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from make_queue.models.models import Reservation


def reservation_type(reservation, user):
    if reservation.special:
        return "make"
    if reservation.event:
        return "event"
    if user is not None and reservation.user == user:
        return "own"
    return "normal"


def get_reservations(request, machine):
    start_date = parse_datetime(request.GET.get("startDate"))
    end_date = parse_datetime(request.GET.get("endDate"))

    reservations = []
    for reservation in Reservation.objects.filter(machine=machine, start_time__lt=end_date, end_time__gt=start_date):
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
