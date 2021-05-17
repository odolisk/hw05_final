from django.test import TestCase

from posts.models import Post, Group, User


class PostGroupModelsTest(TestCase):

    def test_models_str_methods(self):
        """The Post model __str__ method returns first 15 chars of the post text.
        The Group model __str__ method returns group title."""
        user = User.objects.create(username='testuser')
        group = Group.objects.create(
            title='test_group',
            slug='None',
            description='Тестовая группа'
        )
        post = Post.objects.create(
            text='Тут текст нового поста',
            author=user,
            group=group
        )
        expected_value = {
            post: post.text[:15],
            group: group.title
        }
        for obj, val in expected_value.items():
            with self.subTest():
                self.assertEqual(str(obj), val)
