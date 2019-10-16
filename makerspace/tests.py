from django.test import TestCase

from .models import MakerSpace


# Create your tests here.
class ToolTestCase(TestCase):
    def setUp(self):
        self.first_tool = MakerSpace()

    def test_create_a_tool(self):
        self.first_tool.title = 'test tool'
        self.assertEqual(self.first_tool.title,'test tool')

