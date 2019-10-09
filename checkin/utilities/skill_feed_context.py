from django.utils import timezone

from checkin.models import Profile


expiry_time = 3600 * 3


def is_checkin_expired(profile):
    return (timezone.now() - profile.last_checkin).total_seconds() >= expiry_time


def check_out_expired(profile):
    if is_checkin_expired(profile):
        profile.on_make = False
        profile.save()
        return True
    return False


def get_skill_dict_context():
    skill_dict = {}

    for profile in Profile.objects.filter(on_make=True):
        if check_out_expired(profile):
            continue

        for userskill in profile.userskill_set.all():
            skill = userskill.skill

            if (skill not in skill_dict or userskill.skill_level > skill_dict[skill][0]) \
                    and not is_checkin_expired(profile):
                skill_dict[skill] = (userskill.skill_level, profile.last_checkin)
    return sorted(skill_dict.items(), key=lambda x: x[1][1], reverse=True)
