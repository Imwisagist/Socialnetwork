from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Dimedrol')
        cls.group = Group.objects.create(
            title='Тестовая группа с длинным заголовком',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая очень длинная запись',
        )
        cls.LIMIT_CHARS = 15

    def test_all_models_fields_have_correct_verboses(self) -> None:
        """Все поля моделей имеют корректные verbose_name"""
        post_fields_and_expectations_tuple = (
            ('pub_date', "Дата публикации"),
            ('text', "Текст поста"),
            ('author', "Автор поста"),
            ('group', "Группа поста"),
        )

        for field, expectation in post_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field)
                    .verbose_name, expectation
                )

        test_group_fields_and_expectations_tuple = (
            ('title', "Заголовок"),
            ('slug', "Слаг"),
            ('description', "Описание"),
        )

        for field, expectation in test_group_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field)
                    .verbose_name, expectation
                )

    def test_all_models_fields_have_correct_help_text(self) -> None:
        """Все поля моделей имеют корректные help_text"""
        post_fields_and_expectations_tuple = (
            ('text', "Напишите текст поста"),
            ('author', "Задайте автора поста"),
            ('group', "Задайте группу поста"),
        )

        for field, expectation in post_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expectation
                )

        group_fields_and_expectations_tuple = (
            ('title', "Задайте заголовок для группы"),
            ('slug', "Задайте уникальный адрес группы"),
            ('description', "Задайте описание группы"),
        )

        for field, expectation in group_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field)
                    .help_text, expectation
                )

    def test_models_fields_have_correct_str_and_meta_verboses(self) -> None:
        """Все модели имеют корректные str and meta_verboses"""
        post_fields_and_expectations_tuple = (
            (self.post._meta.verbose_name, "Пост"),
            (self.post._meta.verbose_name_plural, "Посты"),
            (str(self.post), self.post.text[:self.LIMIT_CHARS]),
        )

        for field, expectation in post_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    field, expectation
                )

        group_fields_and_expectations_tuple = (
            (self.group._meta.verbose_name, "Группа"),
            (self.group._meta.verbose_name_plural, "Группы"),
            (str(self.group), self.group.title[:self.LIMIT_CHARS]),
        )

        for field, expectation in group_fields_and_expectations_tuple:
            with self.subTest(field=field):
                self.assertEqual(
                    field, expectation
                )
