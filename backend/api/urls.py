from django.urls import path
from . import views


urlpatterns = [
    path('users/<int:user_id>/', views.users.get_user, name='user'),
    path('users/me/', views.users.me, name='me'),
    path('users/me/avatar/', views.avatar.avatar, name='avatar'),
    path('users/', views.users.UserListView.as_view(), name='users'),

    path('users/set_password/', views.login.set_password, name='set_password'),
    path('auth/token/login/', views.login.login, name='login'),
    path('auth/token/logout/', views.login.logout, name='logout'),

    path('users/subscriptions/',
         views.subscription.subscribtions, name='subscribtions'),
    path('users/<int:author_id>/subscribe/',
         views.subscription.subscribe, name='subscribe'),
]
