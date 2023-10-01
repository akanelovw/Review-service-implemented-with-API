from django.db.models import Sum

from recipes.models import IngredientMeasure


def create_cart(user):
    ingredients = (
        IngredientMeasure.objects
        .filter(recipe__shopping_cart__user=user)
        .values('ingredient')
        .annotate(total_amount=Sum('amount'))
        .values_list(
            'ingredient__name', 'total_amount',
            'ingredient__measurement_unit'
        )
    )
    file_list = []
    [file_list.append(
        '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
    return file_list
