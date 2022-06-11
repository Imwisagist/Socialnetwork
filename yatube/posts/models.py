from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

LIMIT_CHARS = 15


class Group(models.Model):
    title = models.CharField(
        "Заголовок",
        max_length=200,
        help_text='Задайте заголовок для группы',
    )
    slug = models.SlugField(
        "Слаг",
        unique=True,
        help_text='Задайте уникальный адрес группы'
    )
    description = models.TextField(
        "Описание",
        help_text='Задайте описание группы'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title[:LIMIT_CHARS]


class Post(models.Model):
    text = models.TextField(
        "Текст поста",
        help_text='Напишите текст поста'
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста",
        help_text='Задайте автора поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Группа поста",
        help_text='Задайте группу поста'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:LIMIT_CHARS]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост с этим комментарием",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария",
    )
    text = models.TextField("Текст комментария",)
    created = models.DateTimeField(
        "Дата публикации комментария",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)

    def __str__(self):
        return self.text[:LIMIT_CHARS]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор"
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
