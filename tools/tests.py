from django.test import TestCase

from .models import Tool


# Create your tests here.
class ToolTestCase(TestCase):
    def setUp(self):
        self.first_tool = Tool()

    def test_create_a_tool(self):
        self.first_tool.title = 'test tool'
        self.assertEqual(self.first_tool.title,'test tool')

