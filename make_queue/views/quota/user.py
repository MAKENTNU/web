from django.shortcuts import render


def get_user_quota_view(request, user):
    return render(request, "make_queue/quota/quota_user.html", {"user": user})
