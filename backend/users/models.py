from django.contrib.auth.models import AbstractUser
from django.db import models
import django.contrib.auth.password_validation as validators

EMAIL_MAX_LENGTH = 254
CHAR_FIELD_MAX_LENGTH = 150


class User(AbstractUser):
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False
    )
    first_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    last_name = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.email


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
        ]

    def clean(self):
        if self.user == self.user:
            raise validators.ValidationError(
                {'error': ('Подписаться на себя нельзя')}
            )

    def __str__(self):
        return f'{self.user} - {self.author}'
