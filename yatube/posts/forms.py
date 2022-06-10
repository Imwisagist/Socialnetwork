from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", 'image')
        labels = {'group': 'Группа', 'text': 'Сообщение'}
        help_texts = {'group': 'Выберите группу', 'text': 'Введите сообщение'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {'text': 'Комментарий'}
        help_texts = {'text': 'Напишите комментарий'}
