from django.contrib import admin

from checkin.models import Skill, Profile, UserSkill, SuggestSkill


class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    readonly_fields = ('last_checkin',)
    list_display = ('__str__',)


class UserSkillAdmin(admin.ModelAdmin):
    model = UserSkill
    list_display = ('profile', 'skill', 'skill_level')


class SuggestSkillAdmin(admin.ModelAdmin):
    model = SuggestSkill
    list_display = ('title', 'title_en')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Skill)
admin.site.register(UserSkill, UserSkillAdmin)
admin.site.register(SuggestSkill, SuggestSkillAdmin)
