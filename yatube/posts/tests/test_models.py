from django.test import Client, TestCase
from django.db.utils import IntegrityError

from ..models import (
    Comment,
    Follow,
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


class FollowModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.user_author = User.objects.create_user(username='author')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def test_do_not_accept_user_to_follow_itself(self):
        """Проверка, что пользователь не может подписаться сам на себя."""
        with self.assertRaises(IntegrityError):
            Follow.objects.create(user=self.user, author=self.user)

    def test_follower_and_following_persons_should_unique_together(self):
        """Проверка уникальности связки пользователь -
        автор на которого подписался пользователь."""
        Follow.objects.create(user=self.user, author=self.user_author)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(user=self.user, author=self.user_author)

    def test_both_users_can_follow_each_other(self):
        """Проверка, что оба пользователя могут подписаться друг на друга."""
        Follow.objects.create(user=self.user, author=self.user_author)
        Follow.objects.create(user=self.user_author, author=self.user)
        self.assertEqual(Follow.objects.count(), 2)
