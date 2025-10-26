from unittest import TestCase

from ..modelfields import CardNumber, CardNumberField


class CardNumberModelFieldTest(TestCase):
    def test_get_prep_value(self):
        field = CardNumberField()
        self.assertIs(
            field.get_prep_value(""),
            None,
            "The prep value of an empty string should be None",
        )
        self.assertIs(
            field.get_prep_value("       "),
            None,
            "The prep value of a string of space should be None",
        )
        self.assertIs(
            field.get_prep_value("\t\n \t\n   "),
            None,
            "The prep value of a string of whitespace should be None",
        )
        self.assertEqual(
            field.get_prep_value("1234567890"),
            "1234567890",
            "The prep value of a string of digits should be the same string",
        )
        self.assertEqual(
            field.get_prep_value("EM 1234567890"),
            "1234567890",
            "The prep value of an EM number prefixed by EM should be the EM number without the prefix",
        )
        self.assertEqual(
            field.get_prep_value(CardNumber("1234567890")),
            "1234567890",
            "The prep value of a CardNumber object should be its value",
        )

    def test_from_db_value(self):
        field = CardNumberField()
        value = field.from_db_value("1234567890", None, None)
        self.assertIs(
            type(value),
            CardNumber,
            "If the DB value is not empty it should be a CardNumber object",
        )
        self.assertEqual(
            value.number,
            "1234567890",
            "The CardNumber objects should have the EM number as its number",
        )

        self.assertEqual(
            field.from_db_value("", None, None),
            None,
            "An empty DB value should return None",
        )
