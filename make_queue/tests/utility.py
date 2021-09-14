from django.test import RequestFactory


def template_view_get_context_data(view_class, *args, request_user=None, **kwargs):
    view = view_class()
    view.request = request_with_user(request_user)
    return view.get_context_data(*args, **kwargs)


def request_with_user(user):
    request = RequestFactory().get("/ignored_path")
    request.user = user
    return request


def post_request_with_user(user, data=None):
    request = RequestFactory().post("/ignored_path", data or {})
    request.user = user
    return request
