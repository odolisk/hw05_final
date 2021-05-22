import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

USERNAME = 'testuser'
POSTTEXT = 'Тут текст очередного нового поста'


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.group = Group.objects.create(
            title='test',
            slug='test',
            description='test group'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.MEDIA_ROOT))
    def test_valid_form_create_post(self):
        """Valid PostForm create post in posts."""
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
            'text': POSTTEXT,
            'group': PostFormTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostFormTests.group)
        self.assertEqual(post.author, PostFormTests.user)
        self.assertEqual(post.image.name, f'posts/{uploaded.name}')
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_valid_form_saves_edited_post(self):
        """Valid form saves the edited post after submit."""
        group2 = Group.objects.create(
            title='test2',
            slug='test2',
            description='test group2'
        )
        post = Post.objects.create(
            text='Пост для редактирования',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': group2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(USERNAME, post.id)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post', args=(USERNAME, post.id)))
        post = Post.objects.get(pk=post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, group2)
        self.assertEqual(post.author, PostFormTests.user)

    def test_guest_cant_create_new_post(self):
        """Guest can't create new post using form."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст неавторизованного клиента',
            'group': PostFormTests.group.id,
        }
        response = self.client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('login')
                             + '?next='
                             + reverse('posts:new_post'))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_not_available_not_author(self):
        """Edit post page available only
        to authorized author."""
        not_author = User.objects.create_user(username='notauthor')
        authorized_not_author = Client()
        authorized_not_author.force_login(not_author)
        post = Post.objects.create(
            text='Тут текст нового поста',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        group2 = Group.objects.create(
            title='test2',
            slug='test2',
            description='test group 2'
        )
        post_data = {
            'text': 'Текст неавторизированного поста',
            'group': group2,
        }
        response = authorized_not_author.post(
            reverse('posts:post_edit', args=(USERNAME, post.id)),
            data=post_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post', args=(USERNAME, post.id)))
        test_post = Post.objects.get(pk=post.id)
        self.assertNotEqual(test_post.text, post_data['text'])
        self.assertNotEqual(test_post.group, post_data['group'])

    def test_guest_user_cant_comment(self):
        """Guest user can't comment posts."""
        post = Post.objects.create(
            text="Пост для теста неавторизированного коммента",
            author=PostFormTests.user,
            group=PostFormTests.group,
        )
        comments_before = post.comments.count()
        comment_text = {
            'text': 'Попытка неавторизованного коммента',
        }
        anonym_response = self.client.post(
            reverse('posts:add_comment',
                    args=(USERNAME, post.id,)),
            data=comment_text,
            follow=True
        )
        self.assertRedirects(anonym_response,
                             reverse('login')
                             + '?next='
                             + reverse('posts:add_comment',
                                       args=(USERNAME, post.id)))
        self.assertEqual(post.comments.count(), comments_before)

    def test_auth_user_can_comment(self):
        """Authorized user can comment posts."""
        post = Post.objects.create(
            text="Пост для теста авторизированного коммента",
            author=PostFormTests.user,
            group=PostFormTests.group,
        )
        comments_before = post.comments.count()
        comment_text = {
            'text': 'Попытка авторизованного коммента',
        }
        auth_response = self.authorized_client.post(
            reverse('posts:add_comment',
                    args=(USERNAME, post.id,)),
            data=comment_text,
            follow=True
        )
        self.assertRedirects(auth_response,
                             reverse('posts:post',
                                     args=(USERNAME, post.id)))
        self.assertEqual(post.comments.count(), comments_before + 1)
        comment = post.comments.first()
        self.assertEqual(comment.text, comment_text['text'])
        self.assertEqual(comment.author, PostFormTests.user)
        self.assertEqual(comment.created,
                         auth_response.context['comments'].first().created)
