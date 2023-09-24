from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientMeasure, Recipe,
                            ShoppingCart, Tag)
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Follow

from .enums import Enums, Urls
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPaginator
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, PasswordSerializer,
                          RecipeSerializer, TagSerializer, UserSerializer)

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):

    pagination_class = PageNumberPagination
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny, ]

    def get_queryset(self):
        queryset = super(UsersViewSet, self).get_queryset()
        return queryset

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated, )
    )
    def me(self, request):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def set_password(request):
    serializer = PasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменён'},
            status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'error': 'Введите верные данные'},
        status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated, ])
def subscribe(request, pk):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        if user.id == author.id:
            content = {'errors': 'Нельзя подписаться на себя'}
            return Response(
                content,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            Follow.objects.create(user=user, author=author)
        except IntegrityError:
            content = {'errors': 'Вы уже подписаны'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        follows = User.objects.all().filter(id=pk)
        serializer = FollowSerializer(
            follows,
            context={'request': request},
            many=True,
        )
        return Response(*serializer.data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        try:
            subscription = Follow.objects.get(user=user, author=author)
        except ObjectDoesNotExist:
            content = {'errors': 'Вы не подписаны'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return HttpResponse(
            'Успешная отписка',
            status=status.HTTP_204_NO_CONTENT
        )


class SubscriptionsApiView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitPaginator
    serializer_class = FollowSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following__user=user)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitPaginator
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = self.queryset

        tags = self.request.query_params.getlist(Urls.TAGS.value)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        author = self.request.query_params.get(Urls.AUTHOR.value)
        if author:
            queryset = queryset.filter(author=author)

        if self.request.user.is_anonymous:
            return queryset

        is_in_cart = self.request.query_params.get(Urls.SHOPPING_CART)
        if is_in_cart in Enums.TRUE_SEARCH.value:
            queryset = queryset.filter(shopping_cart__user=self.request.user)
        elif is_in_cart in Enums.FALSE_SEARCH.value:
            queryset = queryset.exclude(shopping_cart__user=self.request.user)

        is_favorite = self.request.query_params.get(Urls.FAVORITES)
        if is_favorite in Enums.TRUE_SEARCH.value:
            queryset = queryset.filter(favorites__user=self.request.user)
        if is_favorite in Enums.FALSE_SEARCH.value:
            queryset = queryset.exclude(favorites__user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def unfavorite(self, model, user, pk):
        favorite = model.objects.filter(user=user, recipe__id=pk)
        if favorite.exists():
            favorite.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response({
            'errors': 'Рецепт не в избранном'
        }, status=status.HTTP_400_BAD_REQUEST)

    def in_favorite(self, model, user, pk):
        if not Recipe.objects.filter(id=pk).exists():
            return Response({
                'errors': 'Рецепта не существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже в избранном'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(
            Recipe,
            id=pk
        )
        model.objects.create(
            user=user,
            recipe=recipe
        )
        serializer = FavoriteSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        pagination_class=None
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.in_favorite(Favorite, request.user, pk)
        elif request.method == 'DELETE':
            return self.unfavorite(Favorite, request.user, pk)
        return None

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        pagination_class=None
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.in_favorite(ShoppingCart, request.user, pk)
        elif request.method == 'DELETE':
            return self.unfavorite(ShoppingCart, request.user, pk)
        return None

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, **kwargs):
        user = request.user
        filename = f'{user.username}_shopping_list.txt'
        ingredients = (
            IngredientMeasure.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        file_list = []
        [file_list.append(
            '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
        file = HttpResponse(
            'Cписок покупок:\n' + '\n'.join(file_list),
            content_type='text/plain'
        )
        file['Content-Disposition'] = (f'attachment; filename={filename}')
        return file


class TagsViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('^name',)
    filterset_class = IngredientFilter
    http_method_names = ['get']
