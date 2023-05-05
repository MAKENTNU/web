from django.test import TestCase
from django_hosts import reverse

from faq.models import Category, Question
from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs


class UrlTests(TestCase):

    def setUp(self):
        self.category1 = Category.objects.create(name="Category 1")
        self.category2 = Category.objects.create(name="Category 2")
        self.categories = (self.category1, self.category2)

        self.question1 = Question.objects.create(title="Question 1", answer="Answer to question 1!")
        self.question1.categories.add(self.category1)
        self.question2 = Question.objects.create(title="Question 2", answer="See above.")
        self.question2.categories.add(self.category1, self.category2)
        self.question3 = Question.objects.create(title="Question 3", answer="No :)")
        self.questions = (self.question1, self.question2, self.question3)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('faq_list'), public=True),
            Get(reverse('admin_faq_panel'), public=False),
            Get(reverse('admin_question_list'), public=False),
            Get(reverse('question_create'), public=False),
            *[
                Get(reverse('question_update', args=[question.pk]), public=False)
                for question in self.questions
            ],
            Get(reverse('admin_category_list'), public=False),
            Get(reverse('category_create'), public=False),
            *[
                Get(reverse('category_update', args=[category.pk]), public=False)
                for category in self.categories
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Category, self.categories)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Question, self.questions)
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
