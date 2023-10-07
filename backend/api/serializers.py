import django.core.validators as validators
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .constants import MIN_INGREDIENT_AMOUNT
from recipes.constants import COOKING_TIME_MIN_VALUE
from recipes.models import (Favorite, Ingredient, IngredientMeasure,
                            Recipe, ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        write_only=True,
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class IngredientMeasureSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientMeasure
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientMeasure.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.following.filter(user=user).exists()
        )


class ShowRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientMeasureSerializer(
        source='ingredient_amount',
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.favorites.filter(user_id=user.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.shopping_cart.filter(user_id=user.id).exists()
        )


class FollowSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            try:
                limit_integer = int(limit)
                queryset = queryset[:limit_integer]
            except TypeError as err:
                raise serializers.ValidationError(f'Value must be int {err}')
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = [
            'user',
            'author',
        ]

    def validate_user(self, obj):
        user = self.context['request'].user
        if obj.following.filter(user=user).exists():
            raise serializers.ValidationError({
                'errors': 'Вы уже подписаны на данного пользователя'})
        return obj


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientCreateSerializer(many=True)
    cooking_time = serializers.IntegerField(
        validators=(
            validators.MinValueValidator(
                COOKING_TIME_MIN_VALUE,
                message='Минимум одна минута'
            ),
        )
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        tags_arr = self.initial_data.get('tags')
        if not tags_arr:
            raise serializers.ValidationError('Не указаны тэги')
        if len(tags_arr) != len(set(tags_arr)):
            raise serializers.ValidationError('Теги повторяются')
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Необходим ингридиент'})
        ingredient_array = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_item['id']
            )
            if ingredient in ingredient_array:
                raise serializers.ValidationError(
                    'Ингридиенты повторяются'
                )
            ingredient_array.append(ingredient)
            if int(ingredient_item['amount']) <= MIN_INGREDIENT_AMOUNT:
                raise serializers.ValidationError({
                    'ingredients': (
                        'Масса ингридиента не может быть меньше нуля'
                    )
                })
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredients_array = []
        for ingredient in ingredients:
            ingredients_array.append(
                IngredientMeasure(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        IngredientMeasure.objects.bulk_create(ingredients_array)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return ShowRecipeSerializer(
            instance,
            context={'request': self.context.get('request')},
        ).data


class RecipeListSerializer(RecipeSerializer):
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientMeasureSerializer(
        source='ingredientmeasure_set',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('recipe', 'user'),
            )
        ]

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('recipe', 'user'),
            )
        ]

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
