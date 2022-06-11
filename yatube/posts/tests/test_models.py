from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Follow, Comment

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
        cls.follow = Follow.objects.create(
            user=cls.user, author=cls.post.author
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text="Ахахах! Автор не оч.",
            author=cls.post.author,
        )

    def check_this_bro(self, model_name, tuple_name, field_check):
        for field, expectation in tuple_name:
            if field_check == 'verbose_name':
                test = model_name._meta.get_field(field)
                with self.subTest(field=field):
                    self.assertEqual(
                        test.verbose_name, expectation
                    )
            elif field_check == 'help_text':
                test = model_name._meta.get_field(field)
                with self.subTest(field=field):
                    self.assertEqual(
                        test.help_text, expectation
                    )
            elif field_check == "str and meta":
                with self.subTest(field=field):
                    self.assertEqual(
                        field, expectation
                    )


    def test_all_models_fields_have_correct_verboses(self) -> None:
        """Все поля моделей имеют корректные verbose_name"""
        post_fields_expectations_tuple = (
            ('pub_date', "Дата публикации"),
            ('text', "Текст поста"),
            ('author', "Автор поста"),
            ('group', "Группа поста"),
            ('image', 'Картинка')
        )
        self.check_this_bro(
            self.post, post_fields_expectations_tuple, 'verbose_name'
        )
        group_fields_expectations_tuple = (
            ('title', "Заголовок"),
            ('slug', "Слаг"),
            ('description', "Описание"),
        )
        self.check_this_bro(
            self.group, group_fields_expectations_tuple, 'verbose_name'
        )
        comment_fields_expectations_tuple = (
            ("post", "Пост с этим комментарием"),
            ("author", "Автор комментария"),
            ("text", "Текст комментария"),
            ("created", "Дата публикации комментария"),
        )
        self.check_this_bro(
            self.comment, comment_fields_expectations_tuple, 'verbose_name'
        )

        follow_fields_expectations_tuple = (
            ("user", "Подписчик"),
            ("author", "Автор"),
        )
        self.check_this_bro(
            self.follow, follow_fields_expectations_tuple, 'verbose_name'
        )

    def test_all_models_fields_have_correct_help_text(self) -> None:
        """Все поля моделей имеют корректные help_text"""
        post_fields_expectations_tuple = (
            ('text', "Напишите текст поста"),
            ('author', "Задайте автора поста"),
            ('group', "Задайте группу поста"),
        )
        self.check_this_bro(
            self.post, post_fields_expectations_tuple, 'help_text'
        )
        group_fields_expectations_tuple = (
            ('title', "Задайте заголовок для группы"),
            ('slug', "Задайте уникальный адрес группы"),
            ('description', "Задайте описание группы"),
        )
        self.check_this_bro(
            self.group, group_fields_expectations_tuple, 'help_text'
        )

    def test_models_fields_have_correct_str_and_meta_verboses(self) -> None:
        """Все модели имеют корректные str and meta_verboses"""
        post_fields_expectations_tuple = (
            (self.post._meta.verbose_name, "Пост"),
            (self.post._meta.verbose_name_plural, "Посты"),
            (str(self.post), self.post.text[:self.LIMIT_CHARS]),
        )
        self.check_this_bro(
            self.post, post_fields_expectations_tuple, "str and meta"
        )
        group_fields_expectations_tuple = (
            (self.group._meta.verbose_name, "Группа"),
            (self.group._meta.verbose_name_plural, "Группы"),
            (str(self.group), self.group.title[:self.LIMIT_CHARS]),
        )
        self.check_this_bro(
            self.group, group_fields_expectations_tuple, "str and meta"
        )
        comment_fields_expectations_tuple = (
            (self.comment._meta.verbose_name, 'Комментарий'),
            (self.comment._meta.verbose_name_plural, 'Комментарии'),
            (str(self.comment), self.comment.text[:self.LIMIT_CHARS]),
        )
        self.check_this_bro(
            self.comment, comment_fields_expectations_tuple, "str and meta"
        )
        follow_fields_expectations_tuple = (
            (self.follow._meta.verbose_name, 'Подписка'),
            (self.follow._meta.verbose_name_plural, 'Подписки'),
        )
        self.check_this_bro(
            self.follow, follow_fields_expectations_tuple, "str and meta"
        )
