from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated, IsAdminUser)
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from users.models import Follow
from recipes.models import (Recipe, Tag, Ingredient,
                            Favorite, ShoppingCart, IngredientMeasure)

from .serializers import (FollowSerializer, PasswordSerializer,
                          UserSerializer, RecipeSerializer,
                          TagSerializer, IngredientSerializer,
                          FavoriteSerializer,)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAnAuthor

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
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введите верные данные'},
        status=status.HTTP_400_BAD_REQUEST)


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
    pagination_class = PageNumberPagination
    permission_classes = [IsAnAuthor]
    filterset_class = RecipeFilter
    filter_backends = [DjangoFilterBackend, ]

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
            permission_classes=[IsAuthenticated]
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
            permission_classes=[IsAuthenticated]
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
    permission_classes = (IsAdminUser,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('^name',)
    filterset_class = IngredientFilter
