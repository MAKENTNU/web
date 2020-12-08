from django.test import TestCase
from django_hosts import reverse

from faq.models import Category, Question
from util.test_utils import Get, assert_requesting_paths_succeeds


class UrlTests(TestCase):

    def setUp(self):
        self.category1 = Category.objects.create(name="Category 1")
        self.category2 = Category.objects.create(name="Category 2")

        self.question1 = Question.objects.create(title="Question 1", answer="Answer to question 1!")
        self.question1.categories.add(self.category1)
        self.question2 = Question.objects.create(title="Question 2", answer="See above.")
        self.question2.categories.add(self.category1, self.category2)
        self.question3 = Question.objects.create(title="Question 3", answer="No :)")
        self.questions = (self.question1, self.question2, self.question3)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('faq_list'), public=True),
            Get(reverse('faq_admin_list'), public=False),
            Get(reverse('faq_create'), public=False),
            *[
                Get(reverse('faq_edit', kwargs={'pk': question.pk}), public=False)
                for question in self.questions
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
