from abc import abstractclassmethod

handlers = {}


def run_handlers(user):
    for handler in sorted(handlers.values(), key=lambda h: -h.priority):
        handler.handle(user)


def register_handler(handler, name):
    handlers[name] = handler


def get_handler(name):
    return handlers[name]


class LoginHandler:
    priority = 0

    @abstractclassmethod
    def handle(self, user):
        raise NotImplementedError()


class GetDataHandler(LoginHandler):
    priority = float("inf")

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


register_handler(GetDataHandler(), "dataporten")
