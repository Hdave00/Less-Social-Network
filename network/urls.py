
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # page to show posts for only the users, that the current user is following
    path("following", views.following, name="following"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # API routes below here, correspond to the JS that will make the API call/Fetch API in the JS part/script.js
    # this route will handle the API data passing of the profile page where the initial 10 posts will be displayed with each posts information,
    # on the page
    path("user/<str:user_name>", views.profile_page, name="profile_page"),
    # this api route will handle the data passing of the edit post function, for editing the post made by the user
    path("post/<int:post_id>/edit", views.edit_post, name="edit_post"),
    # this api route will handle the like/unlike logic for liking a post
    path("post/<int:post_id>/like", views.like_post, name="like_post"),
]
