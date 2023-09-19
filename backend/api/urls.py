from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from api.views import (UsersViewSet, set_password, subscribe,
                       SubscriptionsApiView, RecipeViewSet, TagsViewSet, IngredientViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register('recipes', RecipeViewSet)
router.register('tags', TagsViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
     path(
         'users/<int:pk>/subscribe/',
         subscribe,
         name='subscribe'),
     path(
          'auth/token/login/',
          TokenCreateView.as_view(),
          name='login'),
     path(
          'auth/token/logout/',
          TokenDestroyView.as_view(),
          name='logout'),
     path(
          'users/set_password/',
          set_password,
          name='set_password'),
     path('users/subscriptions/', SubscriptionsApiView.as_view()),

     path('', include(router.urls)),
     path('', include('djoser.urls')),
     path('auth/', include('djoser.urls.authtoken')),
]