from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm, CommentForm
from posts.models import (
    Comment,
    Group,
    Post,
    User
)

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def test_create_post_save_in_base(self):
        """Валидная форма создает запись в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                author=self.post.author,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post_resave_post_in_base(self):
        """Валидная форма изменяет пост в базе данных."""
        group2 = Group.objects.create(
            title='Группа2',
            slug='slug2',
            description='Описание2',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста',
            'group': group2.id,
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст поста',
                author=self.post.author,
                group=group2,
            ).exists()
        )

    def test_help_text(self):
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for name, help_text in help_texts.items():
            with self.subTest(help_text=help_text):
                response = PostFormTests.form.fields[name].help_text
                self.assertEquals(response, help_text)


class CommentFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста'
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def test_create_comment_save_in_base(self):
        """Валидная форма создает запись комментария в базе данных."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Текст комментария',).exists()
        )

    def test_help_text(self):
        text_help_text = CommentFormTests.form.fields['text'].help_text
        self.assertEquals(text_help_text, 'Текст комментария')
