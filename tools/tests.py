from django.test import TestCase

from .models import Tool


# Create your tests here.
class Test_a_model(TestCase):
    def setUp(self):
        self.first_tool = Tool()
        # Dette blir lagret til en hver tid:

    def test_create_a_tool(self):
        self.first_tool.title = 'test tool'
        self.assertEqual(self.first_tool.title,'test tool')
