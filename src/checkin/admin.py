from django.contrib import admin

from checkin.models import Profile, Skill, SuggestSkill, UserSkill
from util.admin_utils import DefaultAdminWidgetsMixin


class ProfileAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ("__str__",)

    readonly_fields = ("last_checkin",)


class SkillAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    pass


class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("profile", "skill", "skill_level")


class SuggestSkillAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ("title", "title_en")


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(UserSkill, UserSkillAdmin)
admin.site.register(SuggestSkill, SuggestSkillAdmin)
