from django.core import validators
from django.db import models

from users.models import User
from .constants import (CHAR_FIELD_MAX_LENGTH,
                        RECIPE_TEXT_MAX_LENGTH,
                        HEX_COLOR_FIELD_MAX_LENGTH,
                        COOKING_TIME_MIN_VALUE,
                        INGREDIENT_AMOUNT_MIN_VALUE,
                        DEFAULT_HEX_COLOR, HEX_COLOR_REGULAR_EXPRESSION)


class Tag(models.Model):

    name = models.CharField(
        verbose_name='Название',
        max_length=CHAR_FIELD_MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name='HEX цвет',
        max_length=HEX_COLOR_FIELD_MAX_LENGTH,
        unique=True,
        default=DEFAULT_HEX_COLOR,
        validators=[
            validators.RegexValidator(
                HEX_COLOR_REGULAR_EXPRESSION,
                'Неверный формат цвета'
            )
        ]
    )
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=CHAR_FIELD_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=CHAR_FIELD_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=CHAR_FIELD_MAX_LENGTH
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientMeasure',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tags',
        verbose_name='Тэг'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    text = models.TextField(
        verbose_name='Описание',
        max_length=RECIPE_TEXT_MAX_LENGTH
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=CHAR_FIELD_MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='media/'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки',
        default=COOKING_TIME_MIN_VALUE,
        validators=[validators.MinValueValidator(
            COOKING_TIME_MIN_VALUE, 'Минимум одна минута')],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name'
            )
        ]

    def __str__(self):
        return self.name


class IngredientMeasure(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            validators.MinValueValidator(
                INGREDIENT_AMOUNT_MIN_VALUE,
                message='Ингридиентов не может быть меньше одного'
            ),
        )
    )

    class Meta:
        ordering = ['-id']
        verbose_name_plural = 'Количество ингридиентов'
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingredient_recipe')]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-id']
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            ),
        )

    def __str__(self):
        return f'{self.recipe} - {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopper',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        ordering = ['-user']
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            ),
        )

    def __str__(self):
        return f'{self.recipe} - {self.user}'
