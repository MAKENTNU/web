from django.test import TestCase

from card.modelfields import CardNumber
from ..models import User


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
