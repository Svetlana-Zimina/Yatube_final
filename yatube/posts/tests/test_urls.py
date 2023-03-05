from http import HTTPStatus

from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Group, Post, User


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def test_urls_exists_at_desired_location(self):
        """Проверка доступности адреса."""
        url_status_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.post.author}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/posts/2/': HTTPStatus.NOT_FOUND,
        }
        for url, status_code in url_status_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_create_and_follow_url_exists_at_desired_location(self):
        """Проверка доступности адресов /create/ и /follow/
        для авторизованного пользователя."""
        url_status_code = {
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
        }
        for url, status_code in url_status_code.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_post_edit_url_exists_at_desired_location_for_author(self):
        """Проверка доступности адреса /posts/post.id/edit/ для автора."""
        response = self.authorized_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_templates(self):
        """Проверка шаблона."""
        url_template = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in url_template.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_redirect_not_author_on_profile(self):
        """Проверка редиректа со страницы
        редактирования поста если не автор."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/profile/{self.post.author}/')

    def test_post_create_url_redirect_not_authorized_user_on_login(self):
        """Проверка редиректа со страницы
        создания поста если пользователь не авторизован."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_create_url_redirect_not_authorized_user_on_login(self):
        """Проверка редиректа при комментировании
        если пользователь не авторизован."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
