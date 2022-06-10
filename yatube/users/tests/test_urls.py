from django.test import TestCase, Client
from http import HTTPStatus


class UsersURLTests(TestCase):
    @classmethod
    def setUp(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_users_urls_and_templates(self):
        """Все адреса и шаблоны аутентификации доступны.
        """
        urls_and_templates_for_guest_tuple = (
            ("/auth/signup/", 'signup.html'),
            ("/auth/login/", 'registration/login.html'),
            ("/auth/logout/", 'registration/logged_out.html'),
            ("/auth/password_reset/", 'registration/password_reset_form.html'),
        )
        for url, template in urls_and_templates_for_guest_tuple:
            with self.subTest("Что-то пошло не так на урле", i=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
