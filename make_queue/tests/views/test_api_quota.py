from django.test import TestCase, Client
from django.urls import reverse
from mock import patch

import web
from dataporten.login_handlers import register_handler
from make_queue.util.login_handlers import PrinterHandler


@patch('make_queue.util.login_handlers.post')
class UpdateAllowedTest(TestCase):
    allowed = ["test"]

    class PostRequestMock:
        @staticmethod
        def json():
            return {"allowed": UpdateAllowedTest.allowed}

    def test_incorrect_token(self, post_mock):
        post_mock.return_value = self.PostRequestMock()
        web.settings.queue_token = "Random token"
        printer_handler = PrinterHandler()
        register_handler(printer_handler, "printer_allowed")
        self.assertEqual(post_mock.call_count, 1)
        response = Client().post(reverse("update_allowed_3D_printer"), data={"token": "Invalid token"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(post_mock.call_count, 1)

    def test_correct_token(self, post_mock):
        post_mock.return_value = self.PostRequestMock()
        web.settings.queue_token = "Random token"
        printer_handler = PrinterHandler()
        register_handler(printer_handler, "printer_allowed")
        self.assertEqual(post_mock.call_count, 1)
        response = Client().post(reverse("update_allowed_3D_printer"), data={"token": "Random token"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(post_mock.call_count, 2)
