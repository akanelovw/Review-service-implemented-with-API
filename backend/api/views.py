from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPaginator
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, SubscribeSerializer, TagSerializer,
                          UserSerializer)
from .utils import create_cart

User = get_user_model()


class UsersViewSet(UserViewSet):

    pagination_class = PageNumberPagination
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
            detail=True,
            methods=['POST', 'DELETE'],
            serializer_class=SubscribeSerializer,
            permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            data = {
                'user': user.id,
                'author': author.id
            }
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer = FollowSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    def del_obj(self, model, user, pk):
        favorite = get_object_or_404(model, user=user, recipe__id=pk)
        favorite.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def add_obj(self, model, user, pk):
        if not Recipe.objects.filter(id=pk).exists():
            return Response({
                'errors': 'Рецепта не существует'
            }, status=status.HTTP_400_BAD_REQUEST)
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен'
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
            return self.add_obj(Favorite, request.user, pk)
        elif request.method == 'DELETE':
            return self.del_obj(Favorite, request.user, pk)
        return None

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        pagination_class=None
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(ShoppingCart, request.user, pk)
        elif request.method == 'DELETE':
            return self.del_obj(ShoppingCart, request.user, pk)
        return None

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, **kwargs):
        user = request.user
        filename = f'{user.username}_shopping_list.txt'
        cart = create_cart(user)
        file = HttpResponse(
            'Cписок покупок:\n' + '\n'.join(cart),
            content_type='text/plain'
        )
        file['Content-Disposition'] = (f'attachment; filename={filename}')
        return file


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('^name',)
    filterset_class = IngredientFilter
