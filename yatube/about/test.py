from django.test import TestCase, Client

from http import HTTPStatus


class StaticPagesURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_author_url_exists_at_desired_location(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)
        """Проверка доступности адреса."""
        pages = {
            '/about/author/',
            '/about/tech/',
        }
        for url in pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_url_uses_correct_template(self):
        """Проверка шаблона."""
        url_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
