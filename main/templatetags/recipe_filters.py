from django import template

from main.models import Favorite, ShopList, Subscription

register = template.Library()


@register.filter(name='is_favorite')
def is_favorite(request, recipe):
    """Определяет находится ли рецепт в избранном."""

    if Favorite.objects.filter(
        user=request.user, recipe=recipe
    ).exists():
        return True

    return False


@register.filter(name='is_follower')
def is_follower(request, profile):
    """Определяет подписан ли пользователь на автора."""

    if Subscription.objects.filter(
        user=request.user, author=profile
    ).exists():
        return True

    return False


@register.filter(name='is_in_purchases')
def is_in_purchases(request, recipe):
    """Определяет находится ли рецепт в списке покупок."""

    if ShopList.objects.filter(
        user=request.user, recipe=recipe
    ).exists():
        return True

    return False
