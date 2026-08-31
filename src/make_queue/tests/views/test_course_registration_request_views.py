from datetime import date, timedelta
from http import HTTPStatus

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from make_queue.models.course import (
    CoursePermission,
    CourseRegistrationConfirmation,
    CourseRegistrationRequest,
    Printer3DCourse,
)
from make_queue.models.machine import MachineType
from users.models import User

COURSE_DATE = date(2026, 8, 25)


class TestCourseRegistrationRequestCreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user1", first_name="Ola", last_name="N")
        self.url = reverse("course_registration_request_create")

    def post_request(self, **data):
        return self.client.post(
            self.url, {"course_date": COURSE_DATE.isoformat(), **data}
        )

    def test_requires_being_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_shows_the_form_to_a_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsNone(response.context["existing_registration"])
        self.assertIsNone(response.context["pending_request"])

    def test_submitting_creates_a_pending_request(self):
        self.client.force_login(self.user)
        self.post_request(card_number="0123456789")

        registration_request = CourseRegistrationRequest.objects.get(user=self.user)
        self.assertEqual(
            registration_request.status, CourseRegistrationRequest.Status.PENDING
        )
        self.assertEqual(registration_request.course_date, COURSE_DATE)
        self.assertEqual(registration_request.card_number.number, "0123456789")

    def test_a_request_does_not_grant_access_to_the_3d_printers(self):
        self.client.force_login(self.user)
        self.post_request(card_number="0123456789")

        self.user.refresh_from_db()
        self.assertFalse(Printer3DCourse.objects.exists())
        self.assertFalse(MachineType.can_use_3d_printer(self.user))
        # The card number should not be moved onto the user before approval either
        self.assertIsNone(self.user.card_number)

    def test_cannot_submit_a_second_request(self):
        self.client.force_login(self.user)
        self.post_request()
        self.post_request()

        self.assertEqual(CourseRegistrationRequest.objects.count(), 1)

    def test_shows_the_pending_request_instead_of_the_form(self):
        CourseRegistrationRequest.objects.create(
            user=self.user, course_date=COURSE_DATE
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertIsNotNone(response.context["pending_request"])

    def test_shows_the_existing_registration_instead_of_the_form(self):
        Printer3DCourse.objects.create(username=self.user.username, date=COURSE_DATE)
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertIsNotNone(response.context["existing_registration"])

    def test_every_active_confirmation_must_be_ticked(self):
        first = CourseRegistrationConfirmation.objects.create(text="I know the rules")
        CourseRegistrationConfirmation.objects.create(text="I know the emergency stop")
        self.client.force_login(self.user)

        response = self.post_request(confirmations=[first.pk])

        self.assertTrue(response.context["form"].errors)
        self.assertFalse(CourseRegistrationRequest.objects.exists())

    def test_ticking_every_confirmation_is_recorded_on_the_request(self):
        confirmations = [
            CourseRegistrationConfirmation.objects.create(text="I know the rules"),
            CourseRegistrationConfirmation.objects.create(text="I know the stop"),
        ]
        self.client.force_login(self.user)

        self.post_request(confirmations=[c.pk for c in confirmations])

        registration_request = CourseRegistrationRequest.objects.get(user=self.user)
        self.assertCountEqual(registration_request.confirmations.all(), confirmations)

    def test_inactive_confirmations_do_not_have_to_be_ticked(self):
        CourseRegistrationConfirmation.objects.create(
            text="No longer relevant", active=False
        )
        self.client.force_login(self.user)

        self.post_request()

        self.assertTrue(CourseRegistrationRequest.objects.exists())

    def test_card_number_of_someone_else_is_rejected(self):
        User.objects.create_user("user2", card_number="0123456789")
        self.client.force_login(self.user)
        response = self.post_request(card_number="0123456789")

        self.assertTrue(response.context["form"].errors)
        self.assertFalse(CourseRegistrationRequest.objects.exists())

    def test_course_date_in_the_future_is_rejected(self):
        self.client.force_login(self.user)
        tomorrow = timezone.localdate() + timedelta(days=1)
        response = self.client.post(self.url, {"course_date": tomorrow.isoformat()})

        self.assertTrue(response.context["form"].errors)
        self.assertFalse(CourseRegistrationRequest.objects.exists())


class TestCourseRegistrationRequestAdminViews(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True)
        self.user = User.objects.create_user("user1", first_name="Ola", last_name="N")
        self.registration_request = CourseRegistrationRequest.objects.create(
            user=self.user, course_date=COURSE_DATE, card_number="0123456789"
        )

        self.list_url = reverse("course_registration_request_list")
        self.approve_url = reverse(
            "course_registration_request_approve", args=[self.registration_request.pk]
        )
        self.reject_url = reverse(
            "course_registration_request_reject", args=[self.registration_request.pk]
        )

    def test_list_requires_permission(self):
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(self.list_url).status_code, HTTPStatus.FORBIDDEN
        )

        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.list_url).status_code, HTTPStatus.OK)

    def test_approving_requires_permission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.approve_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(Printer3DCourse.objects.exists())

    def test_approving_creates_the_registration(self):
        raise3d = CoursePermission.objects.get(short_name="R3DP")
        self.client.force_login(self.superuser)
        self.client.post(self.approve_url, {"course_permissions": [raise3d.pk]})

        registration = Printer3DCourse.objects.get(username=self.user.username)
        self.assertEqual(registration.date, COURSE_DATE)
        self.assertEqual(registration.status, Printer3DCourse.Status.REGISTERED)
        self.assertSetEqual(set(registration.permission_names), {"3DPR", "R3DP"})

        self.registration_request.refresh_from_db()
        self.assertEqual(
            self.registration_request.status,
            CourseRegistrationRequest.Status.APPROVED,
        )

    def test_approving_gives_the_user_access_and_their_card_number(self):
        self.client.force_login(self.superuser)
        self.client.post(self.approve_url)

        self.user.refresh_from_db()
        self.assertTrue(MachineType.can_use_3d_printer(self.user))
        self.assertEqual(self.user.card_number.number, "0123456789")

    def test_approving_an_already_handled_request_does_nothing(self):
        self.client.force_login(self.superuser)
        self.client.post(self.approve_url)
        self.client.post(self.approve_url)

        self.assertEqual(Printer3DCourse.objects.count(), 1)

    def test_approving_a_card_number_that_is_taken_does_nothing(self):
        User.objects.create_user("user2", card_number="0123456789")
        self.client.force_login(self.superuser)
        self.client.post(self.approve_url)

        self.assertFalse(Printer3DCourse.objects.exists())
        self.registration_request.refresh_from_db()
        self.assertEqual(
            self.registration_request.status, CourseRegistrationRequest.Status.PENDING
        )

    def test_rejecting_marks_the_request_as_rejected(self):
        self.client.force_login(self.superuser)
        self.client.post(self.reject_url)

        self.registration_request.refresh_from_db()
        self.assertEqual(
            self.registration_request.status,
            CourseRegistrationRequest.Status.REJECTED,
        )
        self.assertFalse(Printer3DCourse.objects.exists())
