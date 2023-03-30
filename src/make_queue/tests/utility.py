from django.test import RequestFactory


def request_with_user(user):
    request = RequestFactory().get("/ignored_path")
    request.user = user
    return request


def post_request_with_user(user, data=None):
    request = RequestFactory().post("/ignored_path", data or {})
    request.user = user
    return request
