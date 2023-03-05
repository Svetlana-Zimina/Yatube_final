from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import (
    Comment,
    Follow,
    Group,
    Post,
    User
)

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):

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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_author,
            text='Комментарий',
        )
        cls.pages = (
            ('posts:index', 'posts/index.html', None),
            ('posts:group_list', 'posts/group_list.html',
             {'slug': cls.group.slug}),
            ('posts:profile', 'posts/profile.html',
             {'username': cls.post.author}),
            ('posts:post_detail', 'posts/post_detail.html',
             {'post_id': cls.post.id}),
            ('posts:post_create', 'posts/post_create.html', None),
            ('posts:post_edit', 'posts/post_create.html',
             {'post_id': cls.post.id}),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def take_post_and_check(self, response):
        if 'post' in response.context:
            post = response.context['post']
        else:
            post = response.context['page_obj'][0]
        self.assertIsInstance(post, Post)
        self.assertEqual(response.context.get('post').text, 'Пост')
        self.assertEqual(response.context.get('post').author, self.user_author)
        self.assertEqual(response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_page_uses_correct_template(self):
        """URL-адрес использует правильный шаблон."""
        for address in self.pages:
            name_url, template, kwargs = address
            with self.subTest(reverse_name=name_url):
                response = self.authorized_author.get(
                    reverse(name_url, kwargs=kwargs)
                )
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.take_post_and_check(response)

    def test_posts_list_page_show_correct_context(self):
        """Шаблон posts_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.take_post_and_check(response)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        following = Follow.objects.filter(
            author=self.user_author,
            user=self.user
        ).exists()
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.take_post_and_check(response)
        self.assertEqual(response.context['author'], self.user_author)
        self.assertEqual(response.context['following'], following)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.take_post_and_check(response)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertEqual(response.context['comments'][0], self.comment)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.assertIsInstance(response.context['form'], PostForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.assertIsInstance(response.context['form'], PostForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])

    def test_new_post_added_correctly(self):
        """Проверка правильности добавления нового поста."""
        for i in range(0, 2):
            with self.subTest(reverse_name=self.pages[i][0]):
                response = self.authorized_client.get(
                    reverse(self.pages[i][0], kwargs=self.pages[i][2])
                )
                self.assertIn(self.post, response.context['page_obj'])

    def test_new_post_not_on_page_other_group(self):
        """Проверка не добавляется ли новый пост
        на страницу не своей группы."""
        group2 = Group.objects.create(
            title='Группа другая',
            slug='slug2',
            description='Описание другой группы',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{group2.slug}'}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_authorized_user_can_follow_authors(self):
        """Авторизованный пользователь может подписываться на авторов."""
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_author}
            ),
        )
        self.assertTrue(
            Follow.objects.filter(
                author=self.user_author,
                user=self.user
            ).exists()
        )

    def test_authorized_user_can_unfollow_authors(self):
        """Авторизованный пользователь может отписаться от авторов."""
        Follow.objects.create(
            author=self.user_author,
            user=self.user
        )
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_author}
            ),
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.user_author,
                user=self.user
            ).exists()
        )

    def test_new_following_author_post_is_on_follower_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        Follow.objects.create(
            author=self.user_author,
            user=self.user
        )
        new_post = Post.objects.create(
            author=self.user_author,
            text='Новый пост'
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_new_following_author_post_is_not_on_notfollower_page(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        new_post = Post.objects.create(
            author=self.user_author,
            text='Новый пост'
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_cach_work(self):
        """Проверка работы кэширования."""
        response_before = self.authorized_author.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_after = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(
            response_before.content,
            response_after.content
        )
        cache.clear()
        response_after_cach_clear = self.authorized_author.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_before.content, response_after_cach_clear.content
        )


class PaginatorViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POSTS_ON_FIRST_PAGE = settings.POSTS_ON_PAGE
        cls.POSTS_ON_SECOND_PAGE = 1
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание',
        )
        posts_list = []
        for i in range(cls.POSTS_ON_FIRST_PAGE + cls.POSTS_ON_SECOND_PAGE):
            posts_list.append(Post(
                text=f'Текст поста {i}',
                group=cls.group,
                author=cls.user
            ))
        Post.objects.bulk_create(posts_list)
        cls.reverse_names = (
            ('posts:index', None),
            ('posts:group_list', {'slug': cls.group.slug}),
            ('posts:profile', {'username': cls.user}),
        )

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На первую страницу добавляется 10 записей."""
        for address in self.reverse_names:
            name_url, kwargs = address
            with self.subTest(reverse_name=name_url):
                response = self.client.get(
                    reverse(name_url, kwargs=kwargs)
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.POSTS_ON_FIRST_PAGE
                )

    def test_second_page_contains_one_record(self):
        """На вторую страницу добавляется 1 запись."""
        for address in self.reverse_names:
            name_url, kwargs = address
            with self.subTest(reverse_name=name_url):
                response = self.client.get(
                    (reverse(name_url, kwargs=kwargs) + '?page=2')
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.POSTS_ON_SECOND_PAGE
                )
