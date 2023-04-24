from django.test import TestCase
from django_hosts import reverse

from users.models import User
from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from ..models import Profile, Skill, SuggestSkill, UserSkill


class UrlTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2")
        self.profile1 = Profile.objects.create(user=self.user1, on_make=False)
        self.profile2 = Profile.objects.create(user=self.user2, on_make=True)
        self.profiles = (self.profile1, self.profile2)

        self.skill1 = Skill.objects.create(title="Ferdighet 1", title_en="Skill 1")
        self.skill2 = Skill.objects.create(title="Ferdighet 2", title_en="Skill 2")
        self.skills = (self.skill1, self.skill2)

        self.suggest_skill1 = SuggestSkill.objects.create(creator=self.profile1, title="Ferdighet 3", title_en="Skill 3")
        self.suggest_skill2 = SuggestSkill.objects.create(creator=self.profile1, title="Ferdighet 4", title_en="Skill 4")
        self.suggest_skill3 = SuggestSkill.objects.create(creator=self.profile2, title="Ferdighet 5", title_en="Skill 5")
        self.suggest_skills = (self.suggest_skill1, self.suggest_skill2, self.suggest_skill3)

        self.user_skill1_1 = UserSkill.objects.create(profile=self.profile1, skill=self.skill1, skill_level=UserSkill.Level.BEGINNER)
        self.user_skill1_2 = UserSkill.objects.create(profile=self.profile1, skill=self.skill2, skill_level=UserSkill.Level.EXPERT)
        self.user_skill2_2 = UserSkill.objects.create(profile=self.profile2, skill=self.skill2, skill_level=UserSkill.Level.EXPERIENCED)
        self.user_skills = (self.user_skill1_1, self.user_skill1_2, self.user_skill2_2)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            # urlpatterns
            Get(reverse('user_skill_list'), public=True),
            Get(reverse('profile_detail'), public=False),

            # adminpatterns
            Get(reverse('admin_suggest_skill'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Profile, self.profiles)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Skill, self.skills)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(SuggestSkill, self.suggest_skills)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(UserSkill, self.user_skills)
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
