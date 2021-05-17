import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User

USERNAME = 'testuser'
USERNAME2 = 'followuser'
POSTTEXT = 'Тут текст нового поста'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):

    @classmethod
    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def setUpClass(cls):
        super().setUpClass()
        # settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.image_path = 'posts/small.gif'
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )
        cls.post = Post.objects.create(
            text=POSTTEXT,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.index = reverse('posts:index')
        cls.new_post = reverse('posts:new_post')
        cls.group_post = reverse('posts:group_posts',
                                 args=(cls.group.slug,))
        cls.profile = reverse('posts:profile',
                              args=(USERNAME,))
        cls.edit = reverse('posts:post_edit',
                           args=(USERNAME, cls.post.id,))
        cls.single_post = reverse('posts:post',
                                  args=(USERNAME, cls.post.id,))
        cls.follow = reverse('posts:follow_index')
        cls.profile_follow = reverse('posts:profile_follow', args=(USERNAME2,))
        cls.profile_unfollow = reverse('posts:profile_unfollow',
                                       args=(USERNAME2,))
        cls.comment = reverse('posts:add_comment',
                              args=(USERNAME, cls.post.id,))
        cls.templates_names = {
            cls.index: 'posts/index.html',
            cls.group_post: 'posts/group.html',
            cls.new_post: 'posts/edit.html',
            cls.profile: 'posts/profile.html',
            cls.edit: 'posts/edit.html',
            cls.single_post: 'posts/post.html',
            cls.follow: 'posts/follow.html'
        }

    @classmethod
    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_views_uses_correct_templates(self):
        """Views are using correct templates."""
        for path, template in self.templates_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(response, template)

    def context_test(self, context, flag):
        """Check if 'page' or 'post' is in context.
        Compare context with test data."""
        self.assertIn(flag, context)
        if flag == 'post':
            post = context[flag]
        else:
            post = context[flag][0]
        self.assertEqual(post.author, PostPagesTests.user)
        self.assertEqual(post.group, PostPagesTests.group)
        self.assertEqual(post.text, POSTTEXT)
        self.assertEqual(post.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(post.image, PostPagesTests.image_path)

    def test_index_use_correct_context(self):
        """Index page has right context."""
        response = self.authorized_client.get(PostPagesTests.index)
        self.context_test(response.context, 'page')
        post_user = response.context['user']
        self.assertEqual(post_user, PostPagesTests.user)

    def test_group_use_correct_context(self):
        """Group post has right context."""
        response = self.authorized_client.get(PostPagesTests.group_post)
        self.context_test(response.context, 'page')
        post_user = response.context['user']
        self.assertIn('group', response.context)
        post_group = response.context['group']
        self.assertEqual(post_user, PostPagesTests.user)
        self.assertEqual(post_group.title, PostPagesTests.group.title)
        self.assertEqual(post_group.description,
                         PostPagesTests.group.description)

    def test_edit_use_correct_context(self):
        """Edit and new post pages are using correct contexts."""
        test_data = (PostPagesTests.new_post,
                     PostPagesTests.edit)
        for url in test_data:
            response = self.authorized_client.get(url)
            self.assertIn('form', response.context)
            form = response.context['form']
            self.assertIsInstance(form, PostForm)
            self.assertIn('post', response.context)

    def test_profile_use_correct_context(self):
        """Profile page is using correct context."""
        response = self.authorized_client.get(PostPagesTests.profile)
        self.context_test(response.context, 'page')
        post_user = response.context['user']
        self.assertIn('author', response.context)
        author = response.context['author']
        self.assertEqual(post_user, PostPagesTests.user)
        self.assertEqual(author, PostPagesTests.user)

    def test_post_use_correct_context(self):
        """Post page is using correct context."""
        response = self.authorized_client.get(PostPagesTests.single_post)
        self.context_test(response.context, 'post')
        self.assertEqual(response.context['user'], PostPagesTests.user)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], PostPagesTests.user)

    def test_paginator_get_limit_posts(self):
        """Index page contains only 10 posts (paging)."""
        number_of_posts = 13
        obj = (Post(text='Christian %s' % post_num,
                    author=PostPagesTests.user,
                    group=PostPagesTests.group)
               for post_num in range(number_of_posts))
        Post.objects.bulk_create(obj, number_of_posts)
        response = self.client.get(PostPagesTests.index)
        self.assertEqual(len(response.context['page']), settings.POST_PER_PAGE)

    def test_post_not_shows_group2(self):
        """Post does not show in the group2 page."""
        group2 = Group.objects.create(
            title='test2',
            slug='test2',
            description='test group 2'
        )
        group2_posts_url = reverse('posts:group_posts', args=(group2.slug,))
        response = self.authorized_client.get(group2_posts_url)
        self.assertEqual(group2.posts_group.count(), 0)
        self.assertEqual(len(response.context['page']), 0)

    def test_cache_index(self):
        """Index page must be cached with key 'index_page'."""
        self.client.get(PostPagesTests.index)
        key = make_template_fragment_key('index_page')
        self.assertTrue(cache.get(key))

    def test_auth_user_can_follow_unfollow(self):
        """User can follow/unfollow other users."""
        User.objects.create(username=USERNAME2)
        self.authorized_client.get(self.profile_follow)
        self.assertTrue(
            Follow.objects.filter(author__username=USERNAME2,
                                  user__username=USERNAME).exists())
        self.authorized_client.get(self.profile_unfollow)
        self.assertFalse(
            Follow.objects.filter(author__username=USERNAME2,
                                  user__username=USERNAME).exists())

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_new_post_shows_only_to_followers(self):
        """New post shows only in feeds of followers."""
        post_user = User.objects.create(username=USERNAME2)

        auth_follow_client = Client()
        auth_follow_client.force_login(PostPagesTests.user)
        auth_follow_client.get(self.profile_follow)

        not_follow_user = User.objects.create(username='iamnotfollow')
        auth_not_follow_client = Client()
        auth_not_follow_client.force_login(not_follow_user)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_follow.gif',
            content=small_gif,
            content_type='image/gif')
        image_path = 'posts/small_follow.gif'

        new_post = Post.objects.create(
            text='Вечная весна в одиночной камере',
            author=post_user,
            group=self.group,
            image=uploaded)

        response = auth_follow_client.get(self.follow)
        self.assertIn('page', response.context)
        self.assertNotEqual(len(response.context['page']), 0)
        post = response.context['page'][0]
        self.assertEqual(post.id, new_post.id)
        self.assertEqual(post.author, new_post.author)
        self.assertEqual(post.group, new_post.group)
        self.assertEqual(post.text, new_post.text)
        self.assertEqual(post.pub_date, new_post.pub_date)
        self.assertEqual(post.image, image_path)

        response = auth_not_follow_client.get(self.follow)
        self.assertIn('page', response.context)
        self.assertEqual(len(response.context['page']), 0)

    def test_only_auth_user_can_comment(self):
        """Only authorized user can comment posts."""
        post_comments_count = Comment.objects.filter(
            post__id=self.post.id).count()
        comment_text = {
            'text': 'Попытка неавторизованного коммента',
        }
        response = self.client.post(
            self.comment,
            data=comment_text,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('login')
                             + '?next='
                             + reverse('posts:add_comment',
                                       args=(USERNAME, self.post.id)))
        self.assertEqual(
            Comment.objects.filter(
                post__id=self.post.id).count(), post_comments_count)
