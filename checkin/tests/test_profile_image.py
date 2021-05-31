# TODO: use custom user model
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import SimpleCookie
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from ..forms import ProfileImageForm
from ..models import Profile
from ..views import EditProfilePictureView


class UploadProfileImageTests(TestCase):

    def setUp(self):
        password = "1234"
        self.user1 = user1 = User.objects.create_user("user1", "user1@makentnu.no", password)
        user2 = User.objects.create_user("user2", "user2@makentnu.no", password)
        self.client1 = Client()
        self.client2 = Client()
        self.client1.login(username=user1.username, password=password)
        self.client2.login(username=user2.username, password=password)

        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.login(username=user1.username, password=password)

        # Use PKs to get updated data from the database
        # (otherwise, the variables representing the DB objects will contain outdated data after e.g. a view has changed the DB)
        self.profile1_pk = Profile.objects.create(user=user1).pk
        self.profile2_pk = Profile.objects.create(user=user2).pk

    @property
    def profile1(self) -> Profile:
        # See comment in `setUp()`
        return Profile.objects.get(pk=self.profile1_pk)

    @property
    def profile2(self) -> Profile:
        return Profile.objects.get(pk=self.profile2_pk)

    def test_valid_image(self):
        image = SimpleUploadedFile("valid_image.jpg", content=bytearray(settings.MAX_UPLOADED_IMAGE_SIZE), content_type="image/jpeg")
        self.assertFalse(self.profile1.image)
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.assertTrue(self.profile1.image)

    def test_too_large_image(self):
        image = SimpleUploadedFile("too_large_image.jpg", content=bytearray(settings.MAX_UPLOADED_IMAGE_SIZE + 1), content_type="image/jpeg")
        self.assertFalse(self.profile1.image)
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.assertFalse(self.profile1.image)

    def test_too_long_image_name(self):
        # TODO: use MOCK_JPG_FILE instead
        image = SimpleUploadedFile(f"{'a' * 100}.jpg", content=bytearray(1), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.assertFalse(self.profile1.image)

        image = SimpleUploadedFile(f"{'a' * 99}.jpg", content=bytearray(1), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.assertTrue(self.profile1.image)

    def test_empty_image_file(self):
        image = SimpleUploadedFile("image.jpg", content=bytearray(0), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.assertFalse(self.profile1.image)

    def test_allowed_file_extensions(self):
        for extension in ProfileImageForm.allowed_extensions:
            file_name = f"image.{extension}"
            image = SimpleUploadedFile(file_name, content=bytearray(1), content_type="application/octet-stream")
            self.client1.post(reverse("profile_picture"), {"image": image})
            self.assertTrue(self.profile1.image.name.endswith(file_name), f"{self.profile1.image.name} does not end with {file_name}")

    def test_disallowed_file_extensions(self):
        some_disallowed_file_extensions = {
            "", ".", ".0123456789ABCDEF", ".bin", ".css", ".gz",
            ".htm", ".html", ".js", ".json", ".exe", ".mp3", ".pdf", ".rar", ".svg",  # SVG is unsafe due to XSS
            ".tar", ".txt", ".weba", ".webm", ".xml", ".zip", ".7z",
        }
        for extension in some_disallowed_file_extensions:
            file = SimpleUploadedFile(f"file{extension}", content=bytearray(1), content_type="application/octet-stream")
            self.client1.post(reverse("profile_picture"), {"image": file})
            self.assertFalse(self.profile1.image, f"Profile has file {self.profile1.image.name} as image")

    def test_old_profile_image_deletion(self):
        # TODO: switch to `simple_jpg` (from #282) if warnings on CI server
        image1 = SimpleUploadedFile("image1.jpg", content=bytearray(1), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image1})
        image1_path = self.profile1.image.path
        self.assertTrue(os.path.isfile(image1_path))

        image2 = SimpleUploadedFile("image2.jpg", content=bytearray(1), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image2})
        image2_path = self.profile1.image.path
        self.assertTrue(os.path.isfile(image2_path))
        self.assertFalse(os.path.exists(image1_path))

    def test_filename_conflicts_between_users(self):
        image = SimpleUploadedFile("image.jpg", content=bytearray(1), content_type="image/jpeg")
        self.client1.post(reverse("profile_picture"), {"image": image})
        self.client2.post(reverse("profile_picture"), {"image": image})
        self.assertNotEqual(self.profile1.image.path, self.profile2.image.path)
        self.assertTrue(os.path.isfile(self.profile1.image.path))
        self.assertTrue(os.path.isfile(self.profile2.image.path))

    # Due to decorators changing the view's CSRF protection/exemption; possibly not really necessary
    def test_csrf_protection(self):
        image = SimpleUploadedFile("image.jpg", content=bytearray(1), content_type="image/jpeg")
        csrf_token = self.csrf_client.get(reverse("profile")).context.get("csrf_token")

        factory = RequestFactory()
        factory.cookies = SimpleCookie(self.csrf_client.cookies)

        def generate_request(extra_data: dict):
            _request = factory.post(reverse("profile_picture"), {"image": image, **extra_data})
            _request.user = self.user1
            return _request

        request = generate_request({})
        response = EditProfilePictureView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.profile1.image)

        request = generate_request({"csrfmiddlewaretoken": csrf_token})
        response = EditProfilePictureView.as_view()(request)
        self.assertEqual(response.status_code, 302)  # TODO: change to 200 once forms + class-based views are implemented?
        self.assertTrue(self.profile1.image)

    def tearDown(self):
        for profile in Profile.objects.all():
            if profile.image:
                profile.image.delete()
