from django.contrib import admin

from recipes.models import (Tag, Ingredient, IngredientMeasure,
                            Favorite, ShoppingCart, Recipe)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'cooking_time',
        'text',
        'tags',
        'image',
        'author',
        'in_favorites'
    )
    list_editable = (
        'name', 'cooking_time', 'tags',
        'image', 'author'
    )
    readonly_fields = ('in_favorites',)
    search_fields = ('name', 'author')
    list_filter = ('tags',)

    @admin.display(description='Тэги')
    def tags(self, obj):
        list_ = [_.name for _ in obj.tags.all()]
        return ', '.join(list_)

    @admin.display(description='В избранном')
    def in_favorites(self, obj):
        return obj.favorites.count()


admin.site.register(Tag)
admin.site.register(IngredientMeasure)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
