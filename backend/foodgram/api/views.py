from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .models import Recipe, Ingredient, Favorite, ShoppingCart, Follow, IngredientInRecipe
from .serializers import (
    RecipeSerializer, RecipeCreateSerializer,
    IngredientSerializer, UserWithRecipesSerializer, SetAvatarSerializer,
    RecipeMinifiedSerializer, CustomUserSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrReadOnly
from django.urls import reverse

User = get_user_model()

PDF_TITLE_X = 100
PDF_TITLE_Y = 750
PDF_ITEM_START_Y = 700
PDF_ITEM_OFFSET = 20
PDF_PAGE_SIZE = A4
PDF_LEFT_MARGIN = 100


class SetAvatarView(views.APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = SetAvatarSerializer(data=request.data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.avatar.delete()
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)


class RecipeListCreateView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save()
    
    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user

        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')

        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=user)

        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(in_shopping_carts__user=user)

        author = self.request.query_params.get('author')
        if author is not None:
            queryset = queryset.filter(author__id=author)

        return queryset


class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


class RecipeShortLinkView(views.APIView):
    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        short_link = request.build_absolute_uri(
            reverse('recipe-detail', kwargs={'pk': recipe.id})
        )
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class FavoriteView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if request.user.favorites.filter(recipe=recipe).exists():
            return Response({"error": "Recipe already in favorites"}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        favorite = request.user.favorites.filter(recipe=recipe)
        if not favorite.exists():
            return Response({"error": "Recipe not in favorites"}, status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if recipe.in_shopping_carts.filter(user=request.user).exists():
            return Response({"error": "Recipe already in shopping cart"}, status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        cart = request.user.shopping_carts.filter(recipe=recipe)
        if not cart.exists():
            return Response({"error": "Recipe not in shopping cart"}, status=status.HTTP_400_BAD_REQUEST)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__in_shopping_carts__user=request.user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=PDF_PAGE_SIZE)
        
        p.drawString(PDF_TITLE_X, PDF_TITLE_Y, "Список покупок")
        
        y_position = PDF_ITEM_START_Y
        for item in ingredients:
            p.drawString(
                PDF_LEFT_MARGIN, 
                y_position, 
                f"{item['ingredient__name']}: {item['total_amount']} {item['ingredient__measurement_unit']}"
            )
            y_position -= PDF_ITEM_OFFSET
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')


class SubscriptionsView(ListAPIView):
    serializer_class = UserWithRecipesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(subscribers__user=self.request.user)


class SubscribeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        author = get_object_or_404(User, id=id)
        if author == request.user:
            return Response({"error": "Cannot subscribe to yourself"}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.subscriptions.filter(author=author).exists():
            return Response({"error": "Already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=request.user, author=author)
        serializer = UserWithRecipesSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        follow = request.user.subscriptions.filter(author=author)
        if not follow.exists():
            return Response({"error": "Not subscribed"}, status=status.HTTP_400_BAD_REQUEST)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    pagination_class = None


class IngredientDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
