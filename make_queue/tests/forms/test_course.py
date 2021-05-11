from django.test import Client, TestCase

from users.models import User
from ...forms import Printer3DCourseForm
from ...models.course import Printer3DCourse


class Printer3DCourseFormTests(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True)
        self.user1 = User.objects.create_user("user1")

        self.superuser_client = Client()
        self.superuser_client.force_login(self.superuser)

    def test_special_card_numbers_are_rejected_by_custom_checks(self):
        def assert_card_number_valid(card_number_: str, valid_: bool):
            form_data = {
                'user': self.user1.pk,
                'date': "2002-02-02",
                'status': Printer3DCourse.Status.REGISTERED,
                'card_number': card_number_,
            }
            form = Printer3DCourseForm(data=form_data)
            self.assertEqual(form.is_valid(), valid_)

        card_number_to_valid = {
            # The phone number of Building security at NTNU
            "91897373": False,
            # Added 1 to the number above
            "91897374": True,
            # The phone number of Building security formatted with spaces
            "918 97 373": False,
        }
        for card_number, valid in card_number_to_valid.items():
            with self.subTest(card_number=card_number):
                assert_card_number_valid(card_number, valid)
                assert_card_number_valid(f" {card_number} ", valid)
                assert_card_number_valid(f"00{card_number}", valid)
