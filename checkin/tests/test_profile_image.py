import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import SimpleCookie
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

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

    def test_allowed_file_extensions(self):
        unknown_file_type = "application/octet-stream"
        some_allowed_file_extensions = {
            "bmp": "image/bmp",
            "gif": "image/gif",
            "ico": "image/vnd.microsoft.icon",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "pdf": "application/pdf",  # Pillow supports PDFs
            "png": "image/png",
            "tif": "image/tiff",
            "tiff": "image/tiff",
            "webp": "image/webp",
            "tga": unknown_file_type,
        }
        some_disallowed_file_extensions = {
            "0123456789ABCDEF": unknown_file_type,
            "bin": unknown_file_type,
            "css": "text/css",
            "gz": "application/gzip",
            "htm": "text/html",
            "html": "text/html",
            "js": "application/javascript",
            "json": "application/json",
            "exe": unknown_file_type,
            "mp3": "audio/mpeg",
            "rar": "application/x-rar-compressed",
            "svg": "image/svg+xml",  # Pillow does not support SVGs
            "tar": "application/x-tar",
            "txt": "text/plain",
            "weba": "audio/webm",
            "webm": "video/webm",
            "xml": "application/xml",
            "zip": "application/zip",
            "7z": "application/x-7z-compressed",
        }

        for extension, content_type in some_allowed_file_extensions.items():
            file_name = f"image.{extension}"
            image = SimpleUploadedFile(file_name, content=bytearray(1), content_type=content_type)
            self.client1.post(reverse("profile_picture"), {"image": image})
            self.assertTrue(self.profile1.image.name.endswith(file_name), f"{self.profile1.image.name} does not end with {file_name}")

        self.profile1.image.delete()

        for extension, content_type in some_disallowed_file_extensions.items():
            file = SimpleUploadedFile(f"file.{extension}", content=bytearray(1), content_type=content_type)
            self.client1.post(reverse("profile_picture"), {"image": file})
            self.assertFalse(self.profile1.image, f"Profile has file {self.profile1.image.name} as image")

    def test_old_profile_image_deletion(self):
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
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.profile1.image)

    def tearDown(self):
        for profile in Profile.objects.all():
            if profile.image:
                profile.image.delete()
