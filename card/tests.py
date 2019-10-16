from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from card.models import Card
from make_queue.models.course import Printer3DCourse


class CardAndCourseSaveTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2")

    def test_user_from_username(self):
        course = Printer3DCourse.objects.create(username=self.user1.username, date=timezone.now(), name=self.user1.get_full_name())
        self.assertEqual(self.user1, course.user)
        self.assertEqual(course.user, course.card.user)

        course.username = "user2"
        course.save()
        self.assertEqual(self.user2, course.user)
        self.assertEqual(course.user, course.card.user)

        course.delete()
        card = Card.objects.filter(user=self.user1)
        self.assertFalse(card.exists())
        card = Card.objects.filter(user=self.user2)
        self.assertTrue(card.exists())

    def test_user_change(self):
        course = Printer3DCourse.objects.create(username=self.user1.username, date=timezone.now(), name=self.user1.get_full_name())
        course.user = self.user2
        course.save()
        # User should be synced
        self.assertEqual(self.user2, course.user)
        self.assertEqual(course.user, course.card.user)
        self.assertEqual(self.user2.username, course.username)

        course.card.user = self.user1
        course.card.save()
        # User should be synced
        self.assertEqual(self.user1, course.card.user)
        self.assertEqual(course.user, course.card.user)
        self.assertEqual(self.user1.username, course.username)

        card_pk = course.card_id
        course.card.user = None
        course.card.save()
        self.assertEqual(course.card.user, None)
        course.refresh_from_db()
        # All fields on card is None, should be deleted
        self.assertEqual(course.card, None)
        card = Card.objects.filter(user=self.user1)
        self.assertFalse(card.exists())
        card = Card.objects.filter(user=self.user2)
        self.assertFalse(card.exists())
        card = Card.objects.filter(pk=card_pk)
        self.assertFalse(card.exists())

    def test_null_card(self):
        card = Card.objects.create(user=None, number=None)
        self.assertTrue(card.pk is None)  # All fields on card is None, should not be saved to database

    def test_set_card(self):
        course = Printer3DCourse.objects.create(username="user3", date=timezone.now(), name="user3")
        self.assertEqual(course.user, None)  # User with username does not exist
        number = "0123456789"
        card = Card.update_or_create(number=number)
        self.assertEqual(card.number, number)
        course.card = card
        course.save()
        self.assertEqual(course.card.number, number)
        card.user = self.user1
        card.save()
        self.assertEqual(card.user, self.user1)
        # User should be synced
        course.refresh_from_db()
        self.assertEqual(course.user, card.user)
        self.assertEqual(course.username, self.user1.username)

    def test_card_connect(self):
        course = Printer3DCourse.objects.create(username="user4", date=timezone.now(), name="user4")
        user4 = User.objects.create_user(username="user4")
        card = Card.update_or_create(number="9876543210", user=user4)
        self.assertEqual(card, user4.card)
        course.refresh_from_db()
        self.assertEqual(card, course.card)
