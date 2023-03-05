from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите картинку',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = 'Категория не выбрана'


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': 'Текст комментария',
        }
