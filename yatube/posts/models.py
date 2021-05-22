from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Наименование', max_length=200,
                             help_text='Введите название группы')
    slug = models.SlugField(verbose_name='Идентификатор URL', unique=True,
                            help_text='Укажите идентификатор URL')
    description = models.TextField(verbose_name='Описание',
                                   help_text='Введите описание группы')

    class Meta:
        verbose_name = 'Группа записей'
        verbose_name_plural = 'Группы записей'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст',
                            help_text='Введите текст',
                            null=True)
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор',
                               related_name='posts_author')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name='posts_group',
                              verbose_name='Группа',
                              blank=True,
                              null=True,
                              help_text='Выберите '
                              'группу для записи')
    image = models.ImageField(upload_to='posts/',
                              verbose_name='Картинка',
                              blank=True,
                              null=True,
                              help_text='Выберите изображение')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Запись',
                             help_text='Запись')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор',
                               help_text='Автор')
    text = models.TextField(verbose_name='Комментарий',
                            help_text='Введите текст комментария',
                            )
    created = models.DateTimeField('Дата комментария',
                                   auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик',
                             help_text='Подписчик'
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Автор',
                               help_text='Автор'
                               )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(fields=('user', 'author'),
                                    name='follow-users'),
        )

    def __str__(self):
        return f'{self.user.username} to {self.author.username}'
