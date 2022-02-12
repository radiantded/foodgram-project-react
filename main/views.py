import csv
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RecipeCreateForm, RecipeForm
from .models import (Favorite, Ingredient, Recipe, ShopList,
                     Subscription, Tag, User)
from .utils import apply_pagination, get_tags_for_edit, get_tags_list, save_form


def index(request):
    tags_list = get_tags_list(request)
    recipe_list = Recipe.objects.filter(
        tags__value__in=tags_list
    ).select_related(
        'author'
    ).prefetch_related(
        'tags'
    ).distinct()

    paginator, page = apply_pagination(request, recipe_list)

    return render(request, 'index.html', {
        'paginator': paginator,
        'page': page,
        'all_tags': Tag.objects.all(),
        'tags_list': tags_list,
    }
    )


def profile(request, username):
    follow_button = False
    tags_list = get_tags_list(request)
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
    paginator, page = apply_pagination(request, recipes_profile)

    return render(request, "authorRecipe.html", {
        'paginator': paginator,
        'page': page,
        'profile': profile,
        'follow_button': follow_button,
        'all_tags': Tag.objects.all(),
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
            'singlePage.html',
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
    text = request.GET.get('query')
    ingredients = list(Ingredient.objects.filter(
        title__istartswith=text
    ).values('title', 'dimension'))

    return JsonResponse(ingredients, safe=False)


@login_required
def new_recipe(request):
    form = RecipeCreateForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        recipe = save_form(form, request)
        form.save_m2m()
        return redirect(
            'recipe',
            recipe_id=recipe.id,
            username=request.user.username
        )

    return render(request, "formRecipe.html", {
        'form': form,
    })


@login_required
def recipe_edit(request, username, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe_tags = recipe.tags.values_list('value', flat=True)

    if request.user != recipe.author:
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
            recipe = save_form(form, request, edit=True)
            recipe.tags.set(new_tags)
            return redirect(
                'recipe',
                recipe_id=recipe.id,
                username=request.user.username
            )

    form = RecipeForm(instance=recipe)
    return render(request, "formRecipe.html", {
        'form': form,
        'recipe': recipe,
        'all_tags': Tag.objects.all(),
        'recipe_tags': recipe_tags,
    })


@login_required
def recipe_delete(request, username, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    if request.user != recipe.author:
        return redirect(
            "recipe",
            username=username,
            recipe_id=recipe_id
        )

    recipe.delete()
    return redirect("profile", username=username)


@login_required
def favorites(request):
    tags_list = get_tags_list(request)
    recipe_list = Recipe.objects.filter(
        favorite_recipes__user=request.user
    ).filter(
        tags__value__in=tags_list
    ).distinct()

    paginator, page = apply_pagination(request, recipe_list)

    return render(request, "favorites.html", {
        'paginator': paginator,
        'page': page,
        'all_tags': Tag.objects.all(),
        'tags_list': tags_list,
    }
    )


@login_required
@require_http_methods(["POST", "DELETE"])
def change_favorites(request, recipe_id):

    if request.method == "POST":
        recipe_id = json.loads(request.body).get('id')
        recipe = get_object_or_404(
            Recipe, pk=recipe_id
        )

        _, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        return JsonResponse({'success': created})

    elif request.method == "DELETE":
        recipe = get_object_or_404(
            Recipe, pk=recipe_id
        )

        removed = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        return JsonResponse({'success': True if removed else False})


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
    ).values(
        'ingredients__title',
        'ingredients__dimension',
    ).annotate(amount=Sum('ingredients__ingredient_amount__quantity'))

    response = HttpResponse(content_type='txt/csv')
    response['Content-Disposition'] = 'attachment; filename="shop_list.txt"'
    writer = csv.writer(response)

    for item in recipes:
        writer.writerow([f"{item['ingredients__title']} "
                         f"({item['amount']} "
                         f"{item['ingredients__dimension']})"])

    return response


@login_required
@require_http_methods(["POST", "DELETE"])
def purchases(request, recipe_id):

    if request.method == "POST":
        recipe_id = json.loads(request.body).get('id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        _, created = ShopList.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        return JsonResponse({'success': created})

    elif request.method == "DELETE":
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        removed = ShopList.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        return JsonResponse({'success': True if removed else False})


@login_required
@require_http_methods(["POST", "DELETE"])
def subscriptions(request, author_id):

    if request.method == "POST":
        author_id = json.loads(request.body).get('id')
        author = get_object_or_404(User, id=author_id)

        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )

        if request.user == author or not created:
            return JsonResponse({'success': False})

        return JsonResponse({'success': True})

    elif request.method == "DELETE":
        author = get_object_or_404(User, id=author_id)

        removed = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        return JsonResponse({'success': False if not removed else True})


@login_required
def my_follow(request):
    subscriptions = User.objects.filter(
        following__user=request.user
    ).annotate(
        recipe_count=Count(
            'recipes'
        )
    )

    recipes = Recipe.objects.filter(
            author__in=subscriptions)
    paginator, page = apply_pagination(request, subscriptions)

    return render(request, 'myFollow.html', {
        'paginator': paginator,
        'page': page,
        'recipe': recipes,
    }
    )
