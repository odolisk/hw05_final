from django.test import TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates = {
            'about:author_url': 'about/author.html',
            'about:tech_url': 'about/tech.html',
        }

    def test_urls_uses_correct_templates(self):
        """URLs about/author and about/tech uses correct templates."""
        for name, template in AboutURLTests.templates.items():
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertTemplateUsed(response, template)
