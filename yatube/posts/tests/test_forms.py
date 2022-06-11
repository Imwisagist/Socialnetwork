import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ZERO_POSTS = 0
        cls.ONE = 1
        cls.group = Group.objects.create(
            title='Rammstein',
            slug='rammy',
            description='Для любителей творчества Rammstein',
        )
        cls.user = User.objects.create_user(username='Liar')
        cls.post = Post.objects.create(
            text='Выпьем за любовь!',
            author=User.objects.create_user(username='Dima'),
            group=Group.objects.create(
                title='Сборник лучших тостов для застолья',
                slug='osujday_alkohol',
                description='Тосты на все случаи жизни',
            ),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'TRACK:ZICK-ZACK',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                args=(self.post.author.username,)),
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + self.ONE)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)

    def test_author_edit_post(self):
        """Автор может редактировать свой пост"""
        post = Post.objects.first()
        posts_count = Post.objects.count
        form_data = {
            'text': 'TRACK:AUSLANDER',
            'group': self.group.id
        }
        response_edit = self.author_client.post(
            reverse('posts:post_edit', args=(post.id,)),
            data=form_data,
            follow=True,
        )
        post_edited = Post.objects.first()
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertNotEqual(post_edited.text, post.text)
        self.assertNotEqual(post_edited.group, post.group)
        self.assertEqual(post_edited.author, self.post.author)
        self.assertRedirects(
            response_edit,
            reverse('posts:post_detail', args=(self.post.id,)),
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )
        response = self.authorized_client.get(
            reverse("posts:group_posts", args=(self.post.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            len(response.context.get('page_obj').object_list), self.ZERO_POSTS
        )
        self.assertEqual(posts_count, Post.objects.count)

    def test_guest_new_post(self):
        """Неавторизованный пользователь не может создавать посты"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'А можно мне пост написать? Я-Гость',
            'group': self.group.id
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='А можно мне пост написать? Я-Гость').exists())   # НЕТ!
        self.assertEqual(posts_count, Post.objects.count())
        login_url = reverse("users:login")
        reverse_url = reverse("posts:post_create", None)
        response = self.client.get(reverse_url, follow=True)
        self.assertRedirects(
            response,
            f'{login_url}?{REDIRECT_FIELD_NAME}={reverse_url}',
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )

    def test_upload_image(self):
        """При отправке поста с картинкой через форму PostForm
        создаётся запись в базе данных.
        """
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
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded,
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=f"posts/{form_data['image']}"
            ).exists()
        )
