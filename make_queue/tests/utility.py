from django.test import RequestFactory


def template_view_get_context_data(view_class, *args, request_user=None, **kwargs):
    view = view_class()
    view.request = RequestFactory().get("/ignored_path")
    view.request.user = request_user
    return view.get_context_data(*args, **kwargs)
