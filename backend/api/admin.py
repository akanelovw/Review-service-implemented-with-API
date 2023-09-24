from django.contrib import admin

from recipes.models import (Tag, Ingredient, IngredientMeasure,
                            Favorite, ShoppingCart, Recipe)
from users.models import User, Follow

admin.site.register(User)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(IngredientMeasure)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Follow)
admin.site.register(Recipe)
