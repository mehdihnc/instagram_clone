from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Pages d'authentification
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Pages principales
    path('', views.feed, name='feed'),
    path('explore/', views.explore, name='explore'),
    path('p/<int:post_id>/', views.post_detail, name='post_detail'),
    path('p/create/', views.create_post, name='create_post'),
    
    # Profil et paramètres
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('settings/', views.account_settings, name='account_settings'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    
    # Actions AJAX
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    
    # Hashtags
    path('tag/<str:tag_name>/', views.hashtag_posts, name='hashtag_posts'),
    path('search/hashtags/', views.search_hashtags, name='search_hashtags'),
] 