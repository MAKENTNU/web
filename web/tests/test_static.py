from pathlib import Path
from urllib.request import urlopen

from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import LiveServerTestCase, override_settings


MANIFEST_HEX_SUFFIX_REGEX = r"\.[0-9a-f]{12}"


class InterpolatedStaticFilesTests(LiveServerTestCase):
    interpolated_files_to_before_and_after_strings = {
        **{
            f'{favicons_base_folder}/img/favicons/browserconfig.interpolated.xml': [
                ("{% get_relative_static './mstile-150x150.png' %}", rf'\./mstile-150x150{MANIFEST_HEX_SUFFIX_REGEX}\.png')
            ]
            for favicons_base_folder in ('web', 'internal', 'admin')
        },
        **{
            f'{favicons_base_folder}/img/favicons/site.interpolated.webmanifest': [
                ("{% get_relative_static './android-chrome-192x192.png' %}", rf'\./android-chrome-192x192{MANIFEST_HEX_SUFFIX_REGEX}\.png'),
                ("{% get_relative_static './android-chrome-512x512.png' %}", rf'\./android-chrome-512x512{MANIFEST_HEX_SUFFIX_REGEX}\.png'),
            ]
            for favicons_base_folder in ('web', 'internal', 'admin')
        },
    }

    # Requesting static files does for some reason not work with `self.client.get()` - even when subclassing `StaticLiveServerTestCase`
    def request(self, url: str):
        return urlopen(f"{self.live_server_url}{url}")

    def test_manifest_static_files_storage_interpolates_files(self):
        self._test_served_static_files_are_interpolated(is_using_manifest=True)

    @override_settings(DEBUG=True)  # False is default when testing
    def test_serve_static_in_debug_interpolates_files(self):
        self._test_served_static_files_are_interpolated(is_using_manifest=False)

    def _test_served_static_files_are_interpolated(self, *, is_using_manifest: bool):
        for interpolated_file, before_and_after_strings in self.interpolated_files_to_before_and_after_strings.items():
            static_filename = static(interpolated_file)
            with self.subTest(interpolated_file=static_filename):
                full_filename = finders.find(interpolated_file)
                file_contents = Path(full_filename).read_text()
                with self.request(static_filename) as response:
                    served_file_contents = response.read().decode()
                for before_string, after_string in before_and_after_strings:
                    self.assertIn(before_string, file_contents)
                    if not is_using_manifest:
                        # Remove the manifest regex, as when in debug mode,
                        # static files are served directly from the source directory (instead of from the `STATIC_ROOT` directory)
                        after_string = after_string.replace(MANIFEST_HEX_SUFFIX_REGEX, "")
                    self.assertRegex(served_file_contents, after_string)
