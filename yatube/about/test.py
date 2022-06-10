from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus


class StaticPagesUrlViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.urls_templates_reverse_names = (
            ('author/', 'about/author.html', 'about:author'),
            ('tech/', 'about/tech.html', 'about:tech'),
        )

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_template_reverse_available(self):
        """Проверка доступности адреса, шаблона и реверса для
        /about/author/ и /about/tech.
        """
        for url, template, reverse_name in self.urls_templates_reverse_names:
            with self.subTest("Что-то пошло не так на урле", i=url):
                response = self.guest_client.get(f'/about/{url}')
                self.assertEqual(response.status_code, HTTPStatus.OK.value)
                self.assertEqual(reverse(reverse_name), f'/about/{url}')
                self.assertTemplateUsed(response, template)
