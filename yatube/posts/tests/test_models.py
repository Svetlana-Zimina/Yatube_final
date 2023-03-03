from django.test import TestCase

from ..models import (
    Comment,
    Group,
    Post,
    User
)


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group = Group.objects.create(
            title='Группа',
            slug='Слаг',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=(
                'Сказка про девочку Женю, которой подарили '
                'волшебный цветик-семицветик. '
                'На нем было семь лепестков, и он мог '
                'выполнить любые семь желаний.'
            ),
        )

    def test_post_str(self):
        """Проверка метода __str__ модели Post."""
        post = PostModelTest.post
        expected_text = post.text[:15]
        self.assertEqual(expected_text, str(post))


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа',
            slug='Слаг',
            description='Описание',
        )

    def test_group_str(self):
        """Проверка метода __str__ модели Group."""
        group = GroupModelTest.group
        expected_title = group.title
        self.assertEqual(expected_title, str(group))


class CommentModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария',
        )

    def test_comment_str(self):
        """Проверка метода __str__ модели Comment."""
        comment = CommentModelTest.comment
        expected_text = comment.text
        self.assertEqual(expected_text, str(comment))
