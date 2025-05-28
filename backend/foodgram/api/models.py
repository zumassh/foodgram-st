from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='users/', null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        ordering = ['username']

class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, through='IngredientInRecipe')
    cooking_time = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_favorite')
        ]

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_shopping_cart')
        ]

class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'], name='unique_follow')
        ]