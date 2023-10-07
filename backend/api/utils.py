from django.db.models import Sum, F

from recipes.models import IngredientMeasure


def create_cart(user):
    ingredients = IngredientMeasure.objects.select_related(
            'recipe', 'ingredient'
        )
    ingredients = ingredients.values(
        'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            ingredient_name=F('ingredient__name'),
            measure=F('ingredient__measurement_unit'),
            total_amount=Sum('amount')
        ).order_by('-ingredient_name')
    file_list = '\n'.join([
        f"{item['ingredient_name']} - {item['total_amount']} {item['measure']}"
        for item in ingredients
    ])
    return file_list
