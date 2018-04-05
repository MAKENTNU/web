from abc import abstractclassmethod
from django.core.cache import cache


def run_handlers(user):
    for handler in sorted(get_handlers().values(), key=lambda h: -h.priority):
        handler.handle(user)


def register_handler(handler_class, name):
    handlers = get_handlers()
    if name not in handlers:
        handlers[name] = handler_class()
    set_cache(handlers)


def get_handler(name):
    handlers = get_handlers()
    return handlers[name] if name in handlers else None


def update_handler(name):
    handlers = get_handlers()
    if name in handlers:
        handlers[name].update()
        set_cache(handlers)


def get_handlers():
    handlers = cache.get("login_handlers")
    if handlers is not None:
        return handlers
    set_cache({})
    return cache.get("login_handlers")


def set_cache(handler):
    cache.set("login_handlers", handler, None)


class LoginHandler:
    priority = 0

    @abstractclassmethod
    def handle(self, user):
        raise NotImplementedError()

    def update(self):
        pass


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


register_handler(GetDataHandler, "dataporten")
