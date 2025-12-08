from datetime import datetime
from http import HTTPStatus

from django.templatetags.static import static
from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_hosts import reverse

from users.models import User
from ...forms.machine import AddMachineForm, ChangeMachineForm
from ...models.course import CoursePermission, Printer3DCourse
from ...models.machine import Machine, MachineType


class TestMachineListView(TestCase):
    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.sewing_machine_type = MachineType.objects.get(pk=2)

        self.machine_list_url = reverse("machine_list")

    def get_machine_list_response(self):
        response = self.client.get(self.machine_list_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return response

    @staticmethod
    def get_shown_machine_type_list(response):
        # Filter the machine types the same way as in the template
        return list(
            machine_type
            for machine_type in response.context["machine_types"]
            if machine_type.shown_machines
        )

    def test_no_machines(self):
        response = self.get_machine_list_response()
        self.assertIn("machine_types", response.context)
        self.assertListEqual(self.get_shown_machine_type_list(response), [])

    def test_one_type_of_machine(self):
        printer1 = Machine.objects.create(
            name="test1", machine_type=self.printer_machine_type
        )
        printer2 = Machine.objects.create(
            name="test2", machine_type=self.printer_machine_type
        )

        response = self.get_machine_list_response()
        shown_machine_types = self.get_shown_machine_type_list(response)
        self.assertEqual(len(shown_machine_types), 1)
        shown_printer_machine_type = shown_machine_types[0]
        self.assertEqual(shown_printer_machine_type, self.printer_machine_type)
        self.assertListEqual(
            list(shown_printer_machine_type.shown_machines), [printer1, printer2]
        )

    def test_several_machine_types(self):
        printer1 = Machine.objects.create(
            name="test1", machine_type=self.printer_machine_type
        )
        printer2 = Machine.objects.create(
            name="test2", machine_type=self.printer_machine_type
        )
        sewing = Machine.objects.create(
            name="test", machine_type=self.sewing_machine_type
        )

        response = self.get_machine_list_response()
        shown_machine_types = self.get_shown_machine_type_list(response)
        self.assertEqual(len(shown_machine_types), 2)
        shown_printer_machine_type, shown_sewing_machine_type = shown_machine_types
        self.assertEqual(shown_printer_machine_type, self.printer_machine_type)
        self.assertEqual(shown_sewing_machine_type, self.sewing_machine_type)
        self.assertListEqual(
            list(shown_printer_machine_type.shown_machines), [printer1, printer2]
        )
        self.assertListEqual(list(shown_sewing_machine_type.shown_machines), [sewing])

    def test_internal_machines_are_only_shown_to_privileged_users(self):
        printer1 = Machine.objects.create(
            name="Printer 1", machine_type=self.printer_machine_type
        )
        printer2 = Machine.objects.create(
            name="Printer 2", machine_type=self.printer_machine_type
        )
        printer3_internal = Machine.objects.create(
            name="Printer 3", machine_type=self.printer_machine_type, internal=True
        )
        printer4 = Machine.objects.create(
            name="Printer 4", machine_type=self.printer_machine_type
        )
        sewing1_internal = Machine.objects.create(
            name="Sewing machine 1",
            machine_type=self.sewing_machine_type,
            internal=True,
        )
        sewing2 = Machine.objects.create(
            name="Sewing machine 2", machine_type=self.sewing_machine_type
        )
        scanner1_internal = Machine.objects.create(
            name="Scanner 1", machine_type=MachineType.objects.get(pk=3), internal=True
        )

        # The internal machines should not be shown to anonymous users
        self.assert_machine_list_contains(
            [
                [printer1, printer2, printer4],
                [sewing2],
            ]
        )

        # The internal machines should not be shown to unprivileged users
        user = User.objects.create_user("user1")
        self.client.force_login(user)
        self.assert_machine_list_contains(
            [
                [printer1, printer2, printer4],
                [sewing2],
            ]
        )

        # The internal machines should be shown to MAKE members
        user.add_perms("internal.is_internal")
        self.assert_machine_list_contains(
            [
                [printer1, printer2, printer3_internal, printer4],
                [sewing1_internal, sewing2],
                [scanner1_internal],
            ]
        )

    def test_sla_machines_are_only_shown_to_internal_users_or_users_with_sla_course(
        self,
    ):
        raise3d_printer_machine_type = MachineType.objects.get(pk=6)
        sla_printer_machine_type = MachineType.objects.get(pk=7)

        printer1 = Machine.objects.create(
            name="Printer 1", machine_type=self.printer_machine_type
        )
        raise3d_printer1 = Machine.objects.create(
            name="Raise3dD printer 1", machine_type=raise3d_printer_machine_type
        )
        sla_printer1 = Machine.objects.create(
            name="SLA printer 1", machine_type=sla_printer_machine_type
        )

        # The SLA printer should not be shown to anonymous users
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
            ]
        )

        # The SLA printer should not be shown to "normal" users
        user = User.objects.create_user("user1")
        self.client.force_login(user)
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
            ]
        )

        # The SLA printer should not be shown to users with a standard course
        course = Printer3DCourse.objects.create(user=user, date=timezone.now())
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
            ]
        )

        # The SLA printer should be shown to users with an SLA course
        course.course_permissions.set(
            [
                CoursePermission.objects.get(
                    short_name=CoursePermission.DefaultPerms.SLA_PRINTER_COURSE
                )
            ]
        )
        course.save()
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
                [sla_printer1],
            ]
        )

        # The SLA printer should be shown to MAKE members with an SLA course
        self.assertListEqual(list(user.user_permissions.all()), [])
        user.add_perms("internal.is_internal")
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
                [sla_printer1],
            ]
        )

        # The SLA printer should be shown to MAKE members without an SLA course
        course.delete()
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
                [sla_printer1],
            ]
        )

        # The SLA printer should not be shown to "normal" users, again
        user.user_permissions.set([])
        self.assert_machine_list_contains(
            [
                [printer1],
                [raise3d_printer1],
            ]
        )

    def assert_machine_list_contains(
        self, expected_machines_per_machine_type: list[list[Machine]]
    ):
        response = self.get_machine_list_response()
        shown_machine_types = self.get_shown_machine_type_list(response)
        for machine_type, expected_machines in zip(
            shown_machine_types, expected_machines_per_machine_type, strict=True
        ):
            self.assertListEqual(list(machine_type.shown_machines), expected_machines)

    def test_machines_are_sorted_correctly(self):
        correct_machine_orders = []
        for machine_type in (self.printer_machine_type, self.sewing_machine_type):
            machine_b = self.create_machine("b", machine_type)
            machine_c = self.create_machine("c", machine_type)
            machine_d = self.create_machine("d", machine_type)
            machine_1_h = self.create_machine("h", machine_type, priority=1)
            machine_3_e = self.create_machine("e", machine_type, priority=3)
            machine_2_f = self.create_machine("f", machine_type, priority=2)
            machine_2_g = self.create_machine("g", machine_type, priority=2)
            machine_2_a = self.create_machine("a", machine_type, priority=2)
            correct_machine_orders.append(
                [
                    machine_1_h,
                    machine_2_a,
                    machine_2_f,
                    machine_2_g,
                    machine_3_e,
                    machine_b,
                    machine_c,
                    machine_d,
                ]
            )

        response = self.get_machine_list_response()
        shown_machine_types = self.get_shown_machine_type_list(response)
        for machine_type, correct_machine_order in zip(
            shown_machine_types, correct_machine_orders, strict=True
        ):
            with self.subTest(machine_type=machine_type):
                self.assertListEqual(
                    list(machine_type.shown_machines), correct_machine_order
                )

    def test_get_machine_list_view_contains_img_path_in_html(self):
        def assert_response_contains_num_of_each_img_path(num_of_each: int):
            response = self.client.get(reverse("machine_list"))
            for stream_image_name in ["out_of_order", "no_stream", "maintenance"]:
                with self.subTest(stream_image_name=stream_image_name):
                    self.assertContains(
                        response,
                        static(f"make_queue/img/{stream_image_name}.svg"),
                        count=num_of_each,
                    )

        assert_response_contains_num_of_each_img_path(0)

        self.create_machine(
            name_prefix="available",
            machine_type=self.printer_machine_type,
            status=Machine.Status.AVAILABLE,
        )
        self.create_machine(
            name_prefix="out of order",
            machine_type=self.printer_machine_type,
            status=Machine.Status.OUT_OF_ORDER,
        )
        self.create_machine(
            name_prefix="maintenance",
            machine_type=self.printer_machine_type,
            status=Machine.Status.MAINTENANCE,
        )

        assert_response_contains_num_of_each_img_path(1)

    @staticmethod
    def create_machine(
        name_prefix: str, machine_type: MachineType, **kwargs
    ) -> Machine:
        """Creates a machine of type ``machine_type`` with name '``name_prefix`` ``machine_type``'."""
        return Machine.objects.create(
            name=f"{name_prefix} {machine_type.name}",
            machine_type=machine_type,
            **kwargs,
        )


class TestMachineDetailView(TestCase):
    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        printer_machine_type = MachineType.objects.get(pk=1)
        sewing_machine_type = MachineType.objects.get(pk=2)

        printer1 = Machine.objects.create(
            name="Printer 1",
            machine_model="Ultimaker",
            machine_type=printer_machine_type,
        )
        printer2 = Machine.objects.create(
            name="Printer 2",
            machine_model="Ultimaker",
            machine_type=printer_machine_type,
        )
        sewing_machine1 = Machine.objects.create(
            name="Sewing 1", machine_model="Janome", machine_type=sewing_machine_type
        )
        self.machines = (printer1, printer2, sewing_machine1)

    def test_year_and_week_query_parameters_responds_with_expected_context(self):
        def assert_context_has(
            url: str, *, selected_year: int, selected_week: int, selected_date: datetime
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            context = response.context
            self.assertEqual(context["selected_year"], selected_year)
            self.assertEqual(context["selected_week"], selected_week)
            self.assertEqual(context["selected_date"], selected_date)

        for machine in self.machines:
            with self.subTest(machine=machine):
                base_url = reverse("machine_detail", args=[machine.pk])
                # (`calendar_year=1&calendar_week=1` causes an `OverflowError`, but not consistently in all test environments)
                assert_context_has(
                    f"{base_url}?calendar_year=1&calendar_week=2",
                    selected_year=1,
                    selected_week=2,
                    selected_date=parse_datetime("0001-01-08"),
                )
                # The first week of 2020 started with the last few days of December 2019
                assert_context_has(
                    f"{base_url}?calendar_year=2020&calendar_week=1",
                    selected_year=2020,
                    selected_week=1,
                    selected_date=parse_datetime("2019-12-30"),
                )
                assert_context_has(
                    f"{base_url}?calendar_year=2020&calendar_week=2",
                    selected_year=2020,
                    selected_week=2,
                    selected_date=parse_datetime("2020-01-06"),
                )
                assert_context_has(
                    f"{base_url}?calendar_year=2020&calendar_week=52",
                    selected_year=2020,
                    selected_week=52,
                    selected_date=parse_datetime("2020-12-21"),
                )
                assert_context_has(
                    f"{base_url}?calendar_year=2020&calendar_week=53",
                    selected_year=2020,
                    selected_week=53,
                    selected_date=parse_datetime("2020-12-28"),
                )
                assert_context_has(
                    f"{base_url}?calendar_year=2021&calendar_week=1",
                    selected_year=2021,
                    selected_week=1,
                    selected_date=parse_datetime("2021-01-04"),
                )
                assert_context_has(
                    f"{base_url}?calendar_year=9999&calendar_week=52",
                    selected_year=9999,
                    selected_week=52,
                    selected_date=parse_datetime("9999-12-27"),
                )

    def test_year_and_week_query_parameters_responds_with_expected_errors(self):
        def assert_error_response_contains(url: str, *, expected_json_dict: dict):
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertDictEqual(response.json(), expected_json_dict)

        value_greater_or_equal_1 = "Verdien må være større enn eller lik 1."
        value_less_or_equal_53 = "Verdien må være mindre enn eller lik 53."
        value_less_or_equal_9999 = "Verdien må være mindre enn eller lik 9999."
        value_not_int = "Oppgi et heltall."
        both_fields_must_be_set = {
            "__all__": [
                "Either both 'calendar_year' and 'calendar_week' must be set, or none of them."
            ]
        }
        undefined_asdf_field = {
            "undefined_fields": {
                "message": "These provided fields are not defined in the API.",
                "fields": ["asdf"],
            }
        }
        for machine in self.machines:
            with self.subTest(machine=machine):
                base_url = reverse("machine_detail", args=[machine.pk])
                assert_error_response_contains(
                    f"{base_url}?asdf=asdf", expected_json_dict={**undefined_asdf_field}
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2020&calendar_week=1&asdf=asdf",
                    expected_json_dict={**undefined_asdf_field},
                )

                assert_error_response_contains(
                    f"{base_url}?calendar_year=1&calendar_week=0",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [value_greater_or_equal_1],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2020&calendar_week=-1",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [value_greater_or_equal_1],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2020&calendar_week=0",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [value_greater_or_equal_1],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2019&calendar_week=53",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [
                                "53 is not a valid week number for the year 2019."
                            ]
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2019&calendar_week=1000",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [value_less_or_equal_53],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=9999&calendar_week=53",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [
                                "53 is not a valid week number for the year 9999."
                            ]
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2020&calendar_week=qwer",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [value_not_int],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=2019&calendar_week=53&asdf=asdf",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_week": [
                                "53 is not a valid week number for the year 2019."
                            ]
                        },
                        **undefined_asdf_field,
                    },
                )

                assert_error_response_contains(
                    f"{base_url}?calendar_year=-1&calendar_week=1",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_greater_or_equal_1],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=0&calendar_week=53",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_greater_or_equal_1],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=10000&calendar_week=1",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_less_or_equal_9999],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=qwer&calendar_week=1",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_not_int],
                            **both_fields_must_be_set,
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=qwer&calendar_week=1&asdf=asdf",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_not_int],
                            **both_fields_must_be_set,
                        },
                        **undefined_asdf_field,
                    },
                )

                assert_error_response_contains(
                    f"{base_url}?calendar_year=-0&calendar_week=-0",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_greater_or_equal_1],
                            "calendar_week": [value_greater_or_equal_1],
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=0&calendar_week=54",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_greater_or_equal_1],
                            "calendar_week": [value_less_or_equal_53],
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=10000&calendar_week=0",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_less_or_equal_9999],
                            "calendar_week": [value_greater_or_equal_1],
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=10000&calendar_week=1000",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_less_or_equal_9999],
                            "calendar_week": [value_less_or_equal_53],
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=qwer&calendar_week=asdf",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_not_int],
                            "calendar_week": [value_not_int],
                        }
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=10000&calendar_week=1000&asdf=asdf",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_less_or_equal_9999],
                            "calendar_week": [value_less_or_equal_53],
                        },
                        **undefined_asdf_field,
                    },
                )
                assert_error_response_contains(
                    f"{base_url}?calendar_year=qwer&calendar_week=asdf&asdf=asdf",
                    expected_json_dict={
                        "field_errors": {
                            "calendar_year": [value_not_int],
                            "calendar_week": [value_not_int],
                        },
                        **undefined_asdf_field,
                    },
                )


class TestMachineDetailViewWithInternalMachines(TestCase):
    def test_only_internal_users_can_view_internal_machines(self):
        self.assertGreaterEqual(MachineType.objects.count(), 1)
        for machine_type in MachineType.objects.all():
            with self.subTest(machine_type=machine_type):
                user = User.objects.create_user(username=f"user{machine_type.pk}")
                self.client.force_login(user)

                machine = Machine.objects.create(
                    name=f"{machine_type} 1", machine_type=machine_type
                )
                machine_detail_url = reverse("machine_detail", args=[machine.pk])

                # User should be allowed when machine is not internal
                response = self.client.get(machine_detail_url)
                expected_status_code = HTTPStatus.OK
                # ...except if the machine requires the SLA course
                if (
                    machine_type.usage_requirement.pk
                    == CoursePermission.objects.get(
                        short_name=CoursePermission.DefaultPerms.SLA_PRINTER_COURSE
                    ).pk
                ):
                    expected_status_code = HTTPStatus.NOT_FOUND
                self.assertEqual(response.status_code, expected_status_code)

                # User should not be able to find the machine when it's internal
                machine.internal = True
                machine.save()
                response = self.client.get(machine_detail_url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

                # User should be allowed when they're internal
                user.add_perms("internal.is_internal")
                response = self.client.get(machine_detail_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TestMachineCreateAndUpdateView(TestCase):
    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)
        self.user.add_perms(
            "internal.is_internal",
            "make_queue.add_machine",
            "make_queue.change_machine",
        )
        self.client.login(username=username, password=password)

    def test_machine_update_has_correct_form_in_context_data(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        machine = Machine.objects.create(
            name="Test",
            machine_model="Ultimaker 2+",
            machine_type=printer_machine_type,
        )
        response = self.client.get(reverse("machine_update", args=[machine.pk]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(isinstance(response.context_data["form"], ChangeMachineForm))

    def test_machine_create_has_correct_form_in_context_data(self):
        response = self.client.get(reverse("machine_create"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(isinstance(response.context_data["form"], AddMachineForm))
