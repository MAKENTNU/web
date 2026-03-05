from django.test import TestCase

from card.modelfields import CardNumber
from users.models import User


class UserModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1")

    def test_card_number_field_has_expected_value(self):
        card_number = "0123456789"
        self.user1.card_number = card_number
        self.user1.save()
        self.user1.refresh_from_db()

        self.assertIs(type(self.user1.card_number), CardNumber)
        self.assertEqual(self.user1.card_number.number, card_number)
        self.assertEqual(str(self.user1.card_number), f"EM {card_number}")

        # A card number that is an empty string should be retrieved as None
        self.user1.card_number = ""
        self.user1.save()
        self.user1.refresh_from_db()

        self.assertEqual(self.user1.card_number, None)

    def test__get_short_full_name(self):
        def check(first_name: str, last_name: str, *, expected: str) -> None:
            self.user1.first_name = first_name
            self.user1.last_name = last_name
            self.assertEqual(self.user1.get_short_full_name(), expected)

        check("", "", expected="")
        check("Ola", "", expected="Ola")
        check("Ola Johan", "", expected="Ola Johan")
        check("", "Nordmann", expected="Nordmann")
        check("", "Johan Nordmann", expected="Johan Nordmann")
        check("Ola", "Nordmann", expected="Ola Nordmann")
        check("Ola Johan", "Nordmann", expected="Ola Nordmann")
        check("Ola", "Jakob Nordmann", expected="Ola Nordmann")
        check("Ola Johan", "Jakob Nordmann", expected="Ola Nordmann")
