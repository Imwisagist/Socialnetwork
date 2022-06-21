from django.forms import ModelForm
from django import forms

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

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        # self.fields['text'].widget.attrs['cols'] = 5
        self.fields['text'].widget.attrs['rows'] = 3
