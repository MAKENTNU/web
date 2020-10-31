from django.test import TestCase
from django.utils import timezone

# Create your tests here.
from users.models import User
from make_queue.models.course import Printer3DCourse


class CardAndCourseSaveTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2")

    def test_user_from_username(self):
        course = Printer3DCourse.objects.create(username=self.user1.username, date=timezone.now(),
                                                name=self.user1.get_full_name())
        self.assertEqual(self.user1, course.user)

        course.username = "user2"
        course.save()
        self.assertEqual(self.user2, course.user)

    def test_user_change(self):
        course = Printer3DCourse.objects.create(username=self.user1.username, date=timezone.now(),
                                                name=self.user1.get_full_name())
        course.user = self.user2
        course.save()
        # User should be synced
        self.assertEqual(self.user2, course.user)
        self.assertEqual(self.user2.username, course.username)

        self.user2.username = "user2_new"
        self.user2.save()
        # Call save() to update Printer3DCourse
        course.save()
        self.assertEqual(self.user2.username, course.username)

    def test_set_card_from_course(self):
        course = Printer3DCourse.objects.create(user=self.user1, date=timezone.now(), name=self.user1.get_full_name())
        number = "0123456789"
        course.card_number = number
        course.save()

        # Card number should be set on user, not Printer3DCourse
        self.assertEqual(course.card_number, number)
        self.assertEqual(self.user1.card_number, number)
        self.assertEqual(course._card_number, None)

    def test_set_card_from_user(self):
        course = Printer3DCourse.objects.create(user=self.user1, date=timezone.now(), name=self.user1.get_full_name())
        number = "0123456789"
        self.user1.card_number = number
        self.user1.save()

        # Card number should be set on user, not Printer3DCourse
        self.assertEqual(self.user1.card_number, number)
        self.assertEqual(course.card_number, number)
        self.assertEqual(course._card_number, None)

    def test_non_existent_user(self):
        course = Printer3DCourse.objects.create(username="nonexistent", date=timezone.now(), name="none")
        self.assertEqual(course.user, None)
        number = "9876543210"
        course.card_number = number
        course.save()

        # Card number should be set on Printer3DCourse
        self.assertEqual(course.card_number, number)
        self.assertEqual(course._card_number, number)
