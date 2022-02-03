from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from foodgram.settings import POSTS_PER_PAGE

from .models import Amount, Ingredient, Tag


def get_ingredients(request):
    ingredients = {}
    for key in request.POST:
        if key.startswith('nameIngredient'):
            ing_num = key[15:]
            ingredients[request.POST[key]] = request.POST[
                                                'valueIngredient_' + ing_num]
    return ingredients


def get_tags_for_edit(request):
    data = request.POST.copy()
    tags = []
    for value in ['lunch', 'dinner', 'breakfast']:
        if value in data and data.get(value) == 'on':
            tag = get_object_or_404(Tag, value=value)
            tags.append(tag)
    return tags


def get_tags_list(request):
    tags_list = request.GET.getlist('filters')
    if not tags_list:
        tags_list = ['breakfast', 'lunch', 'dinner']
    return tags_list


def save_form(form, request, edit=False):
    recipe = form.save(commit=False)
    if edit:
        recipe.recipe_amount.all().delete()
    else:
        recipe.author = request.user
    recipe.save()
    ingredients = get_ingredients(request)
    for title, quantity in ingredients.items():
        ingredient = get_object_or_404(Ingredient, title=title)
        amount = Amount(
            recipe=recipe,
            ingredient=ingredient,
            quantity=quantity
        )
        amount.save()
    return recipe


def apply_pagination(request, item_list):
    paginator = Paginator(item_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return paginator, page
