from django import template

from main.models import Favorite, ShopList, Subscription

register = template.Library()


@register.filter(name='is_favorite')
def is_favorite(request, recipe):
    """Определяет находится ли рецепт в избранном."""

    return Favorite.objects.filter(
        user=request.user, recipe=recipe
    ).exists()


@register.filter(name='is_follower')
def is_follower(request, profile):
    """Определяет подписан ли пользователь на автора."""

    return Subscription.objects.filter(
        user=request.user, author=profile
    ).exists()


@register.filter(name='is_in_purchases')
def is_in_purchases(request, recipe):
    """Определяет находится ли рецепт в списке покупок."""

    return ShopList.objects.filter(
        user=request.user, recipe=recipe
    ).exists()
