from make_queue.models import Quota3D


class Old3DPrinterMiddleware:

    def __init__(self, get_response):
        with open("make_queue/old3dprinter.txt", "r") as users_file:
            self.username_list = [entry.strip() for entry in users_file.readlines()[1:]]

        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.username in self.username_list and \
                not Quota3D.get_quota(request.user).can_print:
            quota = Quota3D.get_quota(request.user)
            quota.can_print = True
            quota.save()

        response = self.get_response(request)

        return response
