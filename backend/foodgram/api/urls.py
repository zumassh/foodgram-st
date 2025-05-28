from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/me/', views.UserMeView.as_view(), name='user-me'),
    path('users/me/avatar/', views.SetAvatarView.as_view(), name='set-avatar'),
    path('users/subscriptions/', views.SubscriptionsView.as_view(), name='subscriptions'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:id>/subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('users/set_password/', views.SetPasswordView.as_view(), name='set-password'),
    path('recipes/', views.RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/<int:id>/get-link/', views.RecipeShortLinkView.as_view(), name='recipe-short-link'),
    path('recipes/<int:id>/favorite/', views.FavoriteView.as_view(), name='favorite'),
    path('recipes/<int:id>/shopping_cart/', views.ShoppingCartView.as_view(), name='shopping-cart'),
    path('recipes/download_shopping_cart/', views.DownloadShoppingCartView.as_view(), name='download-shopping-cart'),
    path('ingredients/', views.IngredientListView.as_view(), name='ingredient-list'),
    path('ingredients/<int:pk>/', views.IngredientDetailView.as_view(), name='ingredient-detail'),
    path('auth/token/login/', views.TokenLoginView.as_view(), name='token-login'),
    path('auth/token/logout/', views.TokenLogoutView.as_view(), name='token-logout'),
]