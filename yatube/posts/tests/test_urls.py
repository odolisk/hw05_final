from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

USERNAME = 'testuser'


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )
        cls.test_post = Post.objects.create(
            text='Тут текст нового поста',
            author=cls.user,
            group=cls.group
        )
        post_id = cls.test_post.id
        group_slug = cls.group.title
        cls.test_urls_data = (
            ('/', 'posts:index', None),
            (f'/group/{group_slug}/', 'posts:group_posts', (group_slug,)),
            ('/new/', 'posts:new_post', None),
            (f'/{USERNAME}/', 'posts:profile', (USERNAME,)),
            (f'/{USERNAME}/{post_id}/', 'posts:post', (USERNAME, post_id)),
            (f'/{USERNAME}/{post_id}/edit/', 'posts:post_edit',
             (USERNAME, post_id)),
            ('/follow/', 'posts:follow_index', None),
        )
        cls.guests_deprecated_urls = (
            '/new/',
            f'/{USERNAME}/{post_id}/edit/',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_unavailable_page_raise_404(self):
        """Return 404 Not Found if page is not found."""
        path = reverse('posts:index') + 'raise404/'
        response = self.authorized_client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_absolute_urls_available(self):
        """Absolute URLs must be accessible and equal to reversed."""
        for test_url in self.test_urls_data:
            hard, _, _ = test_url
            with self.subTest(hard=hard):
                response = self.authorized_client.get(hard)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_absolute_equals_reversed(self):
        """Absolute URLs must be equal to its reverse."""
        for test_url in self.test_urls_data:
            hard, rvrs, arguments = test_url
            with self.subTest(hard=hard):
                self.assertEqual(hard, reverse(rvrs, args=arguments))

    def test_redirect_guests(self):
        """Guest users should be redirected
        in case of access to forbidden pages."""
        for url in self.guests_deprecated_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response,
                                     reverse('login')
                                     + '?next=' + url)

    def test_redirect_not_author_edit_post(self):
        """Users should be redirected if they try open edit page
        of thet post which they are not created."""
        user = User.objects.create_user(username='imnotauthor')
        self.auth_client = Client()
        self.auth_client.force_login(user)
        post = self.test_post
        path = reverse('posts:post_edit',
                       args=(post.author.username, post.id)
                       )
        redir_path = reverse('posts:post',
                             args=(post.author.username, post.id))
        response = self.auth_client.get(path)
        self.assertRedirects(response, redir_path)

    def test_redirect_follow_unfollow(self):
        """Absolute follo/unfollow URLs are available.
        Users should be redirected after follow/unfollow."""
        USERNAME2 = 'followuser'
        follow_urls = (
            (f'/{USERNAME2}/follow/',
             'posts:profile_follow', (USERNAME2,),
             'posts:profile', (USERNAME2,),),
            (f'/{USERNAME2}/unfollow/',
             'posts:profile_unfollow', (USERNAME2,),
             'posts:profile', (USERNAME2,),),
        )
        User.objects.create_user(username='followuser')
        for hard, rvrs, arg, rvrs_redir, arg_redir in follow_urls:
            with self.subTest(hard=hard):
                self.assertEqual(hard, reverse(rvrs, args=arg))
                response = self.authorized_client.get(hard)
                self.assertRedirects(
                    response, reverse(rvrs_redir, args=arg_redir))
