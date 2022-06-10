import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ZERO = 0
        cls.ONE = 1
        cls.user = User.objects.create_user(username="Lisa")
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
        cls.post = Post.objects.create(
            text='Отличный текст',
            author=User.objects.create_user(username='Dimaster'),
            group=Group.objects.create(
                title='Фанаты',
                description='Отличное описание группы',
                slug='nice-slug',
            ),
            image=SimpleUploadedFile(
                name='small.gif',
                content=cls.small_gif,
                content_type='image/gif'
            )
        )
        cls.group = Group.objects.create(
            title='Кулинарная',
            description='Учимся готовить разработчиков',
            slug='cook-slug',
        )
        cls.reverse_names_args_flags_tuple = (
            ("posts:index", None, None),
            ("posts:group_posts", (cls.post.group.slug,), None),
            ("posts:profile", (cls.post.author.username,), None),
            ("posts:post_detail", (cls.post.id,), True),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def check_context_bro(self, request, flag=False):
        cache.clear()
        response = self.authorized_client.get(request)
        if flag:
            post = response.context.get('post')
        else:
            post = response.context.get('page_obj')[0]
        with self.subTest("Что-то пошло не так начальник, глянешь?",
                          url=request):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.pub_date, self.post.pub_date)
            self.assertEqual(post.group, self.post.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)

    def test_post_contain_in_correct_group(self):
        """Пост при создании не попадает в другую группу"""
        response = self.author_client.get(reverse("posts:group_posts",
                                                  args=(self.group.slug,)))
        self.assertEqual(
            len(response.context.get('page_obj').object_list), self.ZERO
        )

    def test_edit_and_create_have_correct_context(self):
        """Страницы редактирования и создания поста сформированы
        с правильным контекстом"""
        reverses_and_args_tuple = (
            ("posts:post_create", None),
            ("posts:post_edit", (self.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url, args in reverses_and_args_tuple:
            response = self.author_client.get(reverse(url, args=args))
            with self.subTest("Что-то пошло не так", url=url):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_4_general_pages_contain_correct_context(self):
        """Индекс, группа, профиль и подробности о посте сформированы
        с правильным контекстом.
        """
        for url, args, flag in self.reverse_names_args_flags_tuple:
            with self.subTest(url=url):
                self.check_context_bro(
                    request=reverse(url, args=args), flag=flag
                )

    def test_for_group_posts_and_profile_on_contain_correct_context(self):
        """Страница группы и профиль сформированы с правильным контекстом"""
        for url, args, flag in self.reverse_names_args_flags_tuple:
            with self.subTest("Всё пропало! Всё пропало...", url=url):
                response = self.authorized_client.get(reverse(url, args=args))
                if url == "posts:group_posts":
                    group = response.context.get('group')
                    self.assertEqual(group, self.post.group)
                elif url == "posts:profile":
                    author = response.context.get('author')
                    self.assertEqual(author, self.post.author)

    def test_author_can_delete_own_post(self):
        """Только автор может удалить пост"""
        reverse_name = reverse("posts:post_delete", args=(self.post.id,))
        login_url = reverse("users:login")
        response = self.client.get(reverse_name, follow=True)
        self.assertRedirects(
            response,
            f'{login_url}?{REDIRECT_FIELD_NAME}={reverse_name}',
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )
        response = self.authorized_client.get(reverse_name, follow=True)
        self.assertRedirects(
            response, reverse("posts:post_detail", args=(self.post.id,)),
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )
        posts_count = Post.objects.count()
        response = self.author_client.get(reverse_name, follow=True)
        self.assertEqual(posts_count - self.ONE, Post.objects.count())
        self.assertRedirects(
            response, reverse("posts:profile", args=(self.post.author,)),
            target_status_code=HTTPStatus.OK, status_code=HTTPStatus.FOUND,
        )

    def test_post_image_contain_in_context(self):
        """На страницах ниже изображение передаётся в словаре context
        (Главная, страница группы, подробная информация, профиль)"""
        cache.clear()
        for reverse_name, args, _ in self.reverse_names_args_flags_tuple:
            with self.subTest("Проблема на урле", url=reverse_name):
                response = self.author_client.get(reverse(reverse_name,
                                                          args=args))
                if reverse_name == "posts:post_detail":
                    post = response.context.get('post')
                else:
                    post = response.context.get('page_obj')[0]
                self.assertTrue(post.image)
                self.assertEqual(post.image, self.post.image)

    def test_comment_on_the_record_can_only_authorized_user(self):
        """Комментировать может только авторизованный пользователь"""
        self.authorized_client.post(
            f'/posts/{self.post.id}/comment/',
            {'text': "Лучшему ревьюеру ЯП посвящается!)"},
            follow=True
        )
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertContains(response, 'Лучшему ревьюеру ЯП посвящается!)')
        self.authorized_client.logout()
        self.authorized_client.post(
            f'/posts/{self.post.id}/comment/',
            {'text': "Комментарий от Бабайки"},
            follow=True
        )
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertNotContains(response, 'Комментарий от Бабайки')

    # def test_after_successful_sending_comment_appears_on_the_page(self):
    #     """После успешной отправки комментарий появляется на странице"""
    #     self.authorized_client.post(
    #         f'/posts/{self.post.id}/comment/',
    #         {'text': "И на что тут смотреть? Аффтар выпей яду!"},
    #         follow=True
    #     )
    #     response = self.authorized_client.get(f'/posts/{self.post.id}/')
    #     self.assertContains(response, 'И на что тут смотреть? Аффтар выпей яду!')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POSTS_COUNT = 13
        cls.author = User.objects.create_user(username='Dimentiy')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='nice_slug',
            description='Тестовое описание',
        )
        cls.post_list = []
        for iteration in range(cls.POSTS_COUNT):
            cls.post_list.append(Post(
                text=f'Тестовый пост №{iteration}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.post_list)

        cls.templates_and_reverse_names_tuple = (
            ("posts:index", None),
            ("posts:group_posts", (cls.group.slug,)),
            ("posts:profile", (cls.author.username,)),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_first_page_ten_posts_second_page_three_posts(self):
        """Первая страница содержит 10 постов. Вторая 3"""
        post_count = Post.objects.count()
        pages_and_post_count_tuple = (
            ('?page=1', settings.POSTS_ON_PAGE),
            ('?page=2', post_count - settings.POSTS_ON_PAGE),
        )
        for reverse_name, args in self.templates_and_reverse_names_tuple:
            url = reverse(reverse_name, args=args)
            for page_num, post_on_page in pages_and_post_count_tuple:
                with self.subTest(url=reverse_name):
                    response = self.client.get(f'{url}{page_num}')
                    self.assertEqual(len(response.context.get('page_obj')
                                         .object_list), post_on_page)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Dimentiy', )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Какая же хуёвая теория в ЯП. Нет слов.')
        cls.user = User.objects.create_user(username='Igor')

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_index_cache(self):
        """Тест кэширования главной страницы"""
        response_1 = self.author_client.get(reverse('posts:index'))
        post = Post.objects.first()
        post.text = 'Волосатый кокосик)'
        post.save()
        response_2 = self.author_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ZERO = 0
        cls.ONE = 1

    def setUp(self):
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Я так и не победил временные папки:c'
        )
        self.client_follower = Client()
        self.client_following = Client()
        self.client_follower.force_login(self.user_follower)
        self.client_following.force_login(self.user_following)

    def test_follow(self):
        """Авторизованный пользователь может подписаться"""
        self.client_follower.get(
            reverse('posts:profile_follow',
                    args=(self.user_following.username,))
        )
        self.assertEqual(Follow.objects.all().count(), self.ONE)

    def test_follow_unfollow(self):
        """Авторизованный пользователь может отписаться"""
        self.client_follower.get(
            reverse('posts:profile_unfollow',
                    args=(self.user_following.username,))
        )
        self.assertEqual(Follow.objects.all().count(), self.ZERO)

    def test_subscription_feed(self):
        """Запись появляется только в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_follower.get('/follow/')
        post = response.context["page_obj"][0].text
        self.assertEqual(post, self.post.text)
        response = self.client_following.get('/follow/')
        self.assertNotContains(response, self.post.text)
