from django.db.models import Sum, F

from recipes.models import IngredientMeasure


def create_cart(user):
    ingredients = IngredientMeasure.objects.select_related(
        'recipe', 'ingredient'
    )
    ingredients = ingredients.values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        name=F('ingredient__name'),
        measure=F('ingredient__measurement_unit'),
        total_amount=Sum('amount')).order_by('-name')
    file_list = '\n'.join([
        f"{field['name']} - {field['total_amount']} {field['measure']}"
        for field in ingredients
    ])
    return file_list
