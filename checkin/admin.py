from django.contrib import admin

from .models import Profile, Skill, SuggestSkill, UserSkill


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__',)

    readonly_fields = ('last_checkin',)


class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('profile', 'skill', 'skill_level')


class SuggestSkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_en')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Skill)
admin.site.register(UserSkill, UserSkillAdmin)
admin.site.register(SuggestSkill, SuggestSkillAdmin)
