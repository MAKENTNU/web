from abc import abstractclassmethod

handlers = []


def run_handlers(user):
    for handler in handlers:
        handler.handle(user)


def register_handler(handler):
    handlers.append(handler)


class LoginHandler:

    @abstractclassmethod
    def handle(self, user):
        raise NotImplementedError()


class GetDataHandler(LoginHandler):

    def handle(self, user):
        if not user.first_name:
            try:
                data = user.social_auth.first().extra_data
                user.first_name = ' '.join(data['fullname'].split()[:-1])
                user.last_name = data['fullname'].split()[-1]
                user.username = user.email.split('@')[0]
                user.save()
            except:
                pass


register_handler(GetDataHandler())
