from django.test import TestCase

from .modelfields import CardNumber, CardNumberField


class CardNumberModelFieldTest(TestCase):

    def test_get_prep_value(self):
        field = CardNumberField()
        self.assertEqual("", field.get_prep_value(""), "The prep value of an empty string should be an empty string")
        self.assertEqual("", field.get_prep_value("       "),
                         "The prep value of a string of space should be an empty string")
        self.assertEqual("", field.get_prep_value("\t\n \t\n   "),
                         "The prep value of a string of whitespace should be an empty string")
        self.assertEqual("1234567890", field.get_prep_value("1234567890"),
                         "The prep value of a string of digits should be the same string")
        self.assertEqual("1234567890", field.get_prep_value("EM 1234567890"),
                         "The prep value of an EM number prefixed by EM should be the EM number without the prefix")
        self.assertEqual("1234567890", field.get_prep_value(CardNumber("1234567890")),
                         "The prep value of a CardNumber object should be its value")

    def test_from_db_value(self):
        field = CardNumberField()
        value = field.from_db_value("1234567890", "", "")
        self.assertEqual(CardNumber, type(value), "If the DB value is not empty it should be a CardNumber object")
        self.assertEqual("1234567890", value.number, "The CardNumber objects should have the EM number as its number")

        self.assertEqual(None, field.from_db_value("", "", ""), "An empty DB value should return None")
