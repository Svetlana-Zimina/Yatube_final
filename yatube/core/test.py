from django.test import TestCase, Client


class CoreURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_page_404_uses_custom_template(self):
        """Страница 404 отдает кастомный шаблон."""
        response = self.guest_client.get('/posts/1/')
        self.assertTemplateUsed(response, 'core/404.html')
