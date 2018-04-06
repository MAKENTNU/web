from django.contrib.auth.models import User
from django.test import TestCase
from mock import patch

import web
from make_queue.models import Quota3D
from make_queue.util.login_handlers import PrinterHandler


@patch('make_queue.util.login_handlers.post')
class PrinterHandlerTest(TestCase):
    class PostReturnMock:
        @staticmethod
        def json():
            return {"allowed": ["test", "make_ntnu"]}

    def test_no_token(self, mock_post):
        if "queue_token" in dir(web.settings):
            del web.settings.queue_token
        mock_post.return_value = self.PostReturnMock()
        printer_handler = PrinterHandler()
        self.assertEqual(mock_post.call_count, 0)

        try:
            printer_handler.update()
            self.fail("Update should not be possible without token")
        except ValueError:
            pass

    def test_update_with_token(self, mock_post):
        mock_post.return_value = self.PostReturnMock()
        web.settings.queue_token = "Some_random_token"
        printer_handler = PrinterHandler()
        self.assertEqual(mock_post.call_count, 1)
        printer_handler.update()
        self.assertEqual(mock_post.call_count, 2)

    def test_is_correct_token(self, mock_post):
        mock_post.return_value = self.PostReturnMock()
        web.settings.queue_token = "Some_random_token"
        printer_handler = PrinterHandler()
        self.assertEqual(mock_post.call_count, 1)
        self.assertTrue(printer_handler.is_correct_token("Some_random_token"))
        self.assertFalse(printer_handler.is_correct_token("Something_else"))

    def test_update_settings_allowed_user(self, mock_post):
        mock_post.return_value = self.PostReturnMock()
        web.settings.queue_token = "Some_random_token"
        user = User.objects.create_user(username="make_ntnu", password="test_pass")
        self.assertFalse(Quota3D.get_quota(user).can_print)
        printer_handler = PrinterHandler()
        printer_handler.handle(user)
        self.assertTrue(Quota3D.get_quota(user).can_print)

    def test_update_settings_not_allowed_user(self, mock_post):
        mock_post.return_value = self.PostReturnMock()
        web.settings.queue_token = "Some_random_token"
        user = User.objects.create_user(username="test_user", password="test_pass")

        self.assertFalse(Quota3D.get_quota(user).can_print)
        printer_handler = PrinterHandler()
        printer_handler.handle(user)
        self.assertFalse(Quota3D.get_quota(user).can_print)

        quota = Quota3D.get_quota(user)
        quota.can_print = True
        quota.save()

        self.assertTrue(Quota3D.get_quota(user).can_print)
        printer_handler.handle(user)
        self.assertTrue(Quota3D.get_quota(user).can_print)