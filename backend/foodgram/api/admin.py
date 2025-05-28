from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart, Follow

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author',)

    def favorites_count(self, obj):
        return obj.favorite_set.count()
    favorites_count.short_description = 'В избранном'

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)

@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
