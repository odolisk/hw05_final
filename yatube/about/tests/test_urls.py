from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_names = {
            'about:author_url': '/about/author/',
            'about:tech_url': '/about/tech/'
        }

    def test_author_tech_available_to_guest(self):
        """Pages about/author and about/tech are available to guests."""
        for path in AboutURLTests.url_names.keys():
            with self.subTest(path=path):
                response = self.client.get(reverse(path))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_absolute_urls_equal_revers(self):
        """URLs /about/author/ and /about/tech/ are equal
        to its reverse."""
        for name, abs_url in AboutURLTests.url_names.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name), abs_url)
