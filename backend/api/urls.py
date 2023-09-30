from api.views import (IngredientViewSet, RecipeViewSet, SubscriptionsApiView,
                       TagsViewSet, UsersViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet)
router.register('recipes', RecipeViewSet)
router.register('tags', TagsViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('users/subscriptions/', SubscriptionsApiView.as_view()),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    # path('users/<int:pk>/subscribe/', subscribe, name='subscribe'),
]
