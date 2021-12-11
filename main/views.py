import csv
import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RecipeCreateForm, RecipeForm
from .models import (Amount, Favorite, Ingredient, Recipe, ShopList,
                     Subscription, Tag, User)
from .utils import get_ingredients, get_tags_for_edit


def index(request):
    tags_list = request.GET.getlist('filters')

    if tags_list == []:
        tags_list = ['breakfast', 'lunch', 'dinner']

    recipe_list = Recipe.objects.filter(
        tags__value__in=tags_list
    ).select_related(
        'author'
    ).prefetch_related(
        'tags'
    ).distinct()

    all_tags = Tag.objects.all()

    paginator = Paginator(recipe_list, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    if request.user.is_authenticated:
        return render(request, 'indexAuth.html', {
            'paginator': paginator,
            'page': page,
            'all_tags': all_tags,
            'tags_list': tags_list,
        }
        )

    return render(request, 'indexNotAuth.html', {
        'paginator': paginator,
        'page': page,
        'all_tags': all_tags,
        'tags_list': tags_list,
    }
    )


def profile(request, username):
    follow_button = False

    tags_list = request.GET.getlist('filters')

    if tags_list == []:
        tags_list = ['breakfast', 'lunch', 'dinner']

    all_tags = Tag.objects.all()

    profile = get_object_or_404(User, username=username)

    recipes_profile = Recipe.objects.filter(
        author=profile
    ).filter(
        tags__value__in=tags_list
    ).select_related(
        'author'
    ).distinct()

    if request.user.is_authenticated and request.user != profile:
        follow_button = True

    paginator = Paginator(recipes_profile, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "authorRecipe.html", {
        'paginator': paginator,
        'page': page,
        'profile': profile,
        'follow_button': follow_button,
        'all_tags': all_tags,
        'tags_list': tags_list,
        }
        )


def recipe_view(request, username, recipe_id):
    owner = False

    recipe = get_object_or_404(
        Recipe, pk=recipe_id
    )

    if not request.user.is_authenticated:
        return render(
            request,
            'singlePageNotAuth.html',
            {'recipe': recipe}
        )

    profile = get_object_or_404(User, username=username)

    if request.user == recipe.author:
        owner = True

    return render(request, 'singlePage.html', {
        'recipe': recipe,
        'owner': owner,
        'profile': profile,
        })


def ingredients(request):
    """
    Функция для подсказки при написании ингредиента в форме создания рецепта
    возвращает JSON с ингредиентами по первым введенным буквам.
    """
    text = request.GET['query']
    ingredients = Ingredient.objects.filter(
        title__istartswith=text
    )

    ing_list = []

    for ing in ingredients:
        ing_dict = {}
        ing_dict['title'] = ing.title
        ing_dict['dimension'] = ing.dimension
        ing_list.append(ing_dict)

    return JsonResponse(ing_list, safe=False)


def new_recipe(request):

    if request.method == "POST":
        form = RecipeCreateForm(
            request.POST or None,
            files=request.FILES or None
        )

        if form.is_valid():

            my_recipe = form.save(commit=False)
            my_recipe.author = request.user
            my_recipe.save()

            ingredients = get_ingredients(request)
            for title, quantity in ingredients.items():
                ingredient = Ingredient.objects.get(title=title)
                amount = Amount(
                    recipe=my_recipe,
                    ingredient=ingredient,
                    quantity=quantity
                )
                amount.save()

            form.save_m2m()
            return redirect(
                'recipe',
                recipe_id=my_recipe.id,
                username=request.user.username
            )

    form = RecipeCreateForm()
    return render(request, "formRecipe.html", {
        'form': form,
    })


@login_required
def recipe_edit(request, username, recipe_id):

    recipe = get_object_or_404(Recipe, pk=recipe_id)
    author = get_object_or_404(User, id=recipe.author_id)
    all_tags = Tag.objects.all()
    recipe_tags = recipe.tags.values_list('value', flat=True)

    if request.user != author:
        return redirect(
            "recipe",
            username=username,
            recipe_id=recipe_id
        )

    if request.method == 'POST':
        new_tags = get_tags_for_edit(request)
        form = RecipeForm(
            request.POST,
            files=request.FILES or None,
            instance=recipe
        )

        if form.is_valid():
            my_recipe = form.save(commit=False)
            my_recipe.author = request.user
            my_recipe.save()
            my_recipe.recipe_amount.all().delete()
            ingredients = get_ingredients(request)
            for title, quantity in ingredients.items():
                ingredient = Ingredient.objects.get(title=title)
                amount = Amount(
                    recipe=my_recipe,
                    ingredient=ingredient,
                    quantity=quantity
                )
                amount.save()

            my_recipe.tags.set(new_tags)
            return redirect(
                'recipe',
                recipe_id=recipe.id,
                username=request.user.username
            )

    form = RecipeForm(instance=recipe)
    return render(request, "formChangeRecipe.html", {
        'form': form,
        'recipe': recipe,
        'all_tags': all_tags,
        'recipe_tags': recipe_tags,
    })


@login_required
def recipe_delete(request, username, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    author = get_object_or_404(User, id=recipe.author_id)

    if request.user != author:
        return redirect(
            "recipe",
            username=username,
            recipe_id=recipe_id
        )

    recipe.delete()
    return redirect("profile", username=username)


@login_required
def favorites(request):
    tags_list = request.GET.getlist('filters')

    if tags_list == []:
        tags_list = ['breakfast', 'lunch', 'dinner']

    all_tags = Tag.objects.all()

    recipe_list = Recipe.objects.filter(
        favorite_recipes__user=request.user
    ).filter(
        tags__value__in=tags_list
    ).distinct()

    paginator = Paginator(recipe_list, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "favorites.html", {
        'paginator': paginator,
        'page': page,
        'all_tags': all_tags,
        'tags_list': tags_list,
    }
    )


@login_required
@require_http_methods(["POST", "DELETE"])
def change_favorites(request, recipe_id):

    # добавить в избранное
    if request.method == "POST":
        recipe_id = json.loads(request.body).get('id')
        recipe = get_object_or_404(
            Recipe, pk=recipe_id
        )

        obj, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
            return JsonResponse({'success': False})

        return JsonResponse({'success': True})

    # удалить из изобранного
    elif request.method == "DELETE":
        recipe = get_object_or_404(
            Recipe, pk=recipe_id
        )

        removed = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if removed:
            return JsonResponse({'success': True})

        return JsonResponse({'success': False})


@login_required
def shop_list(request):
    """Отображение страницы со списком покупок."""
    if request.GET:
        recipe_id = request.GET.get('recipe_id')
        ShopList.objects.get(
            recipe__id=recipe_id
        ).delete()

    purchases = Recipe.objects.filter(shop_list__user=request.user)

    return render(request, "shopList.html", {
        'purchases': purchases,
    }
    )


@login_required
def get_purchases(request):
    """Скачать лист покупок."""
    recipes = Recipe.objects.filter(
        shop_list__user=request.user
    )

    ing: dict = {}

    for recipe in recipes:
        ingredients = recipe.ingredients.values_list(
            'title', 'dimension'
        )
        amount = recipe.recipe_amount.values_list(
            'quantity', flat=True
        )

        for num in range(len(ingredients)):
            title: str = ingredients[num][0]
            dimension: str = ingredients[num][1]
            quantity: int = amount[num]

            if title in ing.keys():
                ing[title] = [ing[title][0] + quantity, dimension]
            else:
                ing[title] = [quantity, dimension]

    response = HttpResponse(content_type='txt/csv')
    response['Content-Disposition'] = 'attachment; filename="shop_list.txt"'
    writer = csv.writer(response)

    for key, value in ing.items():
        writer.writerow([f'{key} ({value[1]}) - {value[0]}'])

    return response


@login_required
@require_http_methods(["POST", "DELETE"])
def purchases(request, recipe_id):

    # добавить в список покупок
    if request.method == "POST":
        recipe_id = json.loads(request.body).get('id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        obj, created = ShopList.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
            return JsonResponse({'success': False})

        return JsonResponse({'success': True})

    # удалить из списка покупок
    elif request.method == "DELETE":
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        removed = ShopList.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if removed:
            return JsonResponse({'success': True})

        return JsonResponse({'success': False})


@login_required
@require_http_methods(["POST", "DELETE"])
def subscriptions(request, author_id):

    # подписаться на автора
    if request.method == "POST":
        author_id = json.loads(request.body).get('id')
        author = get_object_or_404(User, id=author_id)

        obj, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )

        if request.user == author or not created:
            return JsonResponse({'success': False})

        return JsonResponse({'success': True})

    # отписаться от автора
    elif request.method == "DELETE":
        author = get_object_or_404(User, id=author_id)

        removed = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if removed:
            return JsonResponse({'success': True})

        return JsonResponse({'success': False})


@login_required
def my_follow(request):
    subscriptions = User.objects.filter(
        following__user=request.user
    ).annotate(
        recipe_count=Count(
            'recipes'
        )
    )

    recipe: dict = {}
    for sub in subscriptions:
        recipe[sub] = Recipe.objects.filter(
            author=sub
        )[:3]

    paginator = Paginator(subscriptions, 6)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'myFollow.html', {
        'paginator': paginator,
        'page': page,
        'recipe': recipe,
    }
    )
