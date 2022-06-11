from django.urls import reverse
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Group, Post
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME

User = get_user_model()


class PostsURLSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Dimentor')
        cls.user = User.objects.create_user(username='Pavlentiy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='love_long_slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            text='Отличный текст',
            author=cls.author,
            group=cls.group,
        )

        cls.reverse_args_templates_tuple = (
            ("posts:index", None, 'posts/index.html'),
            ("posts:group_posts", (cls.group.slug,), 'posts/group_list.html'),
            ("posts:profile", (cls.author.username,), 'posts/profile.html'),
            ("posts:post_detail", (cls.post.id,), 'posts/post_detail.html'),
            ("posts:post_create", None, 'posts/create_post.html'),
            ("posts:follow_index", None, 'posts/follow.html')
        )
        cls.reverses_args_urls_tuple = (
            ("posts:index", None, '/'),

            ("posts:group_posts", (cls.group.slug,),
             f'/group/{cls.post.group.slug}/'),

            ("posts:profile", (cls.author.username,),
             f'/profile/{cls.post.author}/'),

            ("posts:post_detail", (cls.post.id,),
             f'/posts/{cls.post.id}/'),

            ("posts:post_edit", (cls.post.id,),
             f'/posts/{cls.post.id}/edit/'),

            ("posts:add_comment", (cls.post.id,),
             f'/posts/{cls.post.id}/comment/'),

            ("posts:follow_index", None, '/follow/'),

            ("posts:profile_follow", (cls.author.username,),
             f'/profile/{cls.post.author}/follow/'),

            ("posts:profile_unfollow", (cls.author.username,),
             f'/profile/{cls.post.author}/unfollow/'),

            ("posts:post_delete", (cls.post.id,),
             f'/posts/{cls.post.id}/delete/'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_page_404(self):
        """Неизвестная страница возвращает 404."""
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_all_urls_available_for_author(self):
        """Все адреса доступны автору."""
        redirect_on_profile_tuple = (
            "posts:post_delete",
            "posts:profile_unfollow",
            "posts:profile_follow",
        )
        for reverse_name, args, _ in self.reverses_args_urls_tuple:
            with self.subTest("Что-то пошло не так на урле", url=reverse_name):
                response = self.author_client.get(
                    reverse(reverse_name, args=args)
                )
                if reverse_name in redirect_on_profile_tuple:
                    self.assertRedirects(
                        response, reverse('posts:profile', args=(self.author,)),
                        target_status_code=HTTPStatus.OK,
                        status_code=HTTPStatus.FOUND,
                    )
                elif reverse_name == "posts:add_comment":
                    self.assertRedirects(
                        response, reverse('posts:post_detail', args=args),
                        target_status_code=HTTPStatus.OK,
                        status_code=HTTPStatus.FOUND,
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_available_for_not_author(self):
        """Редактирование поста для НЕавтора приводит к редиректу на страницу
        подробностей, остальные страницы доступны.
        """
        redirect_on_post_detail_reverse_names_tuple = (
            "posts:post_edit",
            "posts:add_comment",
        )
        redirect_on_profile_reverse_names_tuple = (
            "posts:post_delete",
            "posts:profile_follow",
            "posts:profile_unfollow",
        )
        for reverse_name, args, _ in self.reverses_args_urls_tuple:
            with self.subTest("Что-то пошло не так на урле", url=reverse_name):
                if reverse_name in redirect_on_post_detail_reverse_names_tuple:
                    response = self.authorized_client.get(
                        reverse(reverse_name, args=args), follow=True,
                    )
                    self.assertRedirects(
                        response, reverse(
                            'posts:post_detail',
                            args=(self.post.id,)
                        ),
                        target_status_code=HTTPStatus.OK,
                        status_code=HTTPStatus.FOUND,
                    )
                elif reverse_name in redirect_on_profile_reverse_names_tuple:
                    response = self.author_client.get(
                        reverse(reverse_name, args=args), follow=True,
                    )
                    self.assertRedirects(
                        response, reverse(
                            'posts:profile',
                            args=(self.post.author,)
                        ),
                        target_status_code=HTTPStatus.OK,
                        status_code=HTTPStatus.FOUND,
                    )
                else:
                    response = self.author_client.get(
                        reverse(reverse_name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_available_for_guest(self):
        """С адресов в кортеже redirect происходит переадресация,
        остальные адреса доступны для анонима.
        """
        redirect_urls_tuple = (
            "posts:post_create",
            "posts:post_edit",
            "posts:add_comment",
            "posts:follow_index",
            "posts:profile_follow",
            "posts:profile_unfollow",
            "posts:post_delete"
        )
        for revers, args, _ in self.reverses_args_urls_tuple:
            reverse_name = reverse(revers, args=args)
            login_url = reverse('users:login')
            with self.subTest("Что-то пошло не так на урле", url=revers):
                if revers in redirect_urls_tuple:
                    response = self.client.get(
                        reverse(revers, args=args), follow=True
                    )
                    self.assertRedirects(
                        response,
                        f'{login_url}?{REDIRECT_FIELD_NAME}={reverse_name}',
                        target_status_code=HTTPStatus.OK,
                        status_code=HTTPStatus.FOUND,
                    )
                else:
                    response = self.client.get(reverse(revers, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_reverses_is_correct(self):
        """Все реверсы работают корректно."""
        for reverse_name, args, url in self.reverses_args_urls_tuple:
            with self.subTest("Что-то пошло не так на урле", url=url):
                self.assertEqual(reverse(reverse_name, args=args), url)

    def test_all_templates_correct_use(self):
        """Все шаблоны используются по назначению."""
        for reverse_name, args, template in self.reverse_args_templates_tuple:
            with self.subTest("Что-то пошло не так на урле", url=reverse_name):
                response = self.author_client.get(
                    reverse(reverse_name, args=args)
                )
                self.assertTemplateUsed(response, template)
