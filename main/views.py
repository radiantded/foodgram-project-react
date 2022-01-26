import csv
import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from foodgram.settings import POSTS_PER_PAGE

from .forms import RecipeCreateForm, RecipeForm
from .models import (Amount, Favorite, Ingredient, Recipe, ShopList,
                     Subscription, Tag, User)
from .utils import get_ingredients, get_tags_for_edit


def get_tags_list(request):
    tags_list = request.GET.getlist('filters')
    if not tags_list:
        tags_list = ['breakfast', 'lunch', 'dinner']
    return tags_list


def save_form(form, request, edit=False):
    my_recipe = form.save(commit=False)
    if edit is True:
        my_recipe.recipe_amount.all().delete()
    if edit is False:
        my_recipe.author = request.user
    my_recipe.save()
    ingredients = get_ingredients(request)
    for title, quantity in ingredients.items():
        ingredient = get_object_or_404(Ingredient, title=title)
        amount = Amount(
            recipe=my_recipe,
            ingredient=ingredient,
            quantity=quantity
        )
        amount.save()
    return my_recipe


def index(request):
    tags_list = get_tags_list(request)

    recipe_list = Recipe.objects.filter(
        tags__value__in=tags_list
    ).select_related(
        'author'
    ).prefetch_related(
        'tags'
    ).distinct()

    all_tags = Tag.objects.all()

    paginator = Paginator(recipe_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'paginator': paginator,
        'page': page,
        'all_tags': all_tags,
        'tags_list': tags_list,
    }
    )


def profile(request, username):
    follow_button = False

    tags_list = get_tags_list(request)

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

    paginator = Paginator(recipes_profile, POSTS_PER_PAGE)
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
    ).values())
    return JsonResponse(ingredients, safe=False)


@login_required
def new_recipe(request):
    form = RecipeCreateForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        my_recipe = save_form(form, request)
        form.save_m2m()
        return redirect(
            'recipe',
            recipe_id=my_recipe.id,
            username=request.user.username
        )

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
            my_recipe = save_form(form, request, edit=True)
            my_recipe.tags.set(new_tags)
            return redirect(
                'recipe',
                recipe_id=recipe.id,
                username=request.user.username
            )

    form = RecipeForm(instance=recipe)
    return render(request, "formRecipe.html", {
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
    tags_list = get_tags_list(request)

    all_tags = Tag.objects.all()

    recipe_list = Recipe.objects.filter(
        favorite_recipes__user=request.user
    ).filter(
        tags__value__in=tags_list
    ).distinct()

    paginator = Paginator(recipe_list, POSTS_PER_PAGE)
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

        _, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        return JsonResponse({'success': True if created else False})

    # удалить из изобранного
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

        return JsonResponse({'success': True if created else False})

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

    paginator = Paginator(subscriptions, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'myFollow.html', {
        'paginator': paginator,
        'page': page,
        'recipe': recipes,
    }
    )
