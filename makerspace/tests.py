from django.test import TestCase

from .models import Makerspace


# Create your tests here.
class ToolTestCase(TestCase):
    def setUp(self):
        self.first_tool = Makerspace()

    def test_create_a_tool(self):
        self.first_tool.title = 'test tool'
        self.assertEqual(self.first_tool.title,'test tool')

