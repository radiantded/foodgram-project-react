from django.contrib import admin

from .models import (Amount, Favorite, Ingredient, Recipe, ShopList,
                     Subscription, Tag, User)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'show_favorites')
    list_filter = ('author', 'title', 'tags',)

    def show_favorites(self, obj):
        result = Favorite.objects.filter(recipe=obj).count()
        return result

    show_favorites.short_description = 'Favorite'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('title', 'dimension',)
    list_filter = ('title',)


class UserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'first_name',)


class AmountAdmin(admin.ModelAdmin):
    pass


class FavoriteAdmin(admin.ModelAdmin):
    pass


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')


class ShopListAdmin(admin.ModelAdmin):
    pass


class TagAdmin(admin.ModelAdmin):
    list_display = ('value', 'style', 'name')


admin.site.register(Amount, AmountAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShopList, ShopListAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(User, UserAdmin)
