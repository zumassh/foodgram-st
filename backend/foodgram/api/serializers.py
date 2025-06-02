from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from django.contrib.auth import get_user_model
from .models import Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart, Follow
import base64
from django.core.files.base import ContentFile

User = get_user_model()

MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32_000

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32_000


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)
    
    def to_representation(self, value):
        if not value:
            return ""
        return super().to_representation(value)


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')


class CustomUserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        try:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                return obj.subscriptions.filter(user=request.user).exists()
        except Exception:
            pass
        return False


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientInRecipeCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
        error_messages={
            'min_value': f'Количество ингредиента должно быть не менее {MIN_INGREDIENT_AMOUNT}.',
            'max_value': f'Количество ингредиента не должно превышать {MAX_INGREDIENT_AMOUNT}.'
        }
    )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source='ingredient_amounts')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 
            'author', 
            'ingredients', 
            'is_favorited', 
            'is_in_shopping_cart', 
            'name', 
            'image', 
            'text', 
            'cooking_time']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.in_shopping_carts.filter(user=request.user).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(many=True, write_only=True, required=True)
    image = Base64ImageField()

    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        error_messages={
            'min_value': f'Время приготовления должно быть не менее {MIN_COOKING_TIME} минуты.',
            'max_value': f'Время приготовления не должно превышать {MAX_COOKING_TIME} минут.'
        }
    )

    class Meta:
        model = Recipe
        fields = ['id', 'ingredients', 'image', 'name', 'text', 'cooking_time']
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.method in ['PUT', 'PATCH']:
            if 'ingredients' not in self.initial_data:
                raise serializers.ValidationError({
                    'ingredients': 'Это поле обязательно при обновлении рецепта.'
                })
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Поле ingredients не может быть пустым.")

        seen_ids = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data.get("id")
            amount = ingredient_data.get("amount")

            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f"Ингредиент с id={ingredient_id} не существует."
                )

            if ingredient_id in seen_ids:
                raise serializers.ValidationError(
                    f"Ингредиент с id={ingredient_id} указан несколько раз."
                )
            seen_ids.add(ingredient_id)
        return value
    
    def create_ingredients(self, recipe, ingredients_data):
        ingredients = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients_data:
            instance.ingredients.clear()
            self.create_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipesSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']