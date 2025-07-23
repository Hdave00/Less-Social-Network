import json

# addtiotion 10 v1.0 alpha
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from .models import User, Post


def index(request):
    """ renders the index page, shows all posts and handle new post creation """

    # handle POST request for creating a new post
    if request.method == "POST":
        content = request.POST.get("post-text", "").strip()

        # ensure content is not empty
        if content:
            Post.objects.create(user=request.user, content=content)
            return redirect("index")

    # pagination setup
    max_posts = 10
    # show newest posts first
    posts = Post.objects.all().order_by("-timestamp")

    # check if user has liked post, but non signed in users cant like
    if request.user.is_authenticated:
        for post in posts:
            post.liked_by_user = post.likes.filter(id=request.user.id).exists()
    else:
        for post in posts:
            post.liked_by_user = False

    # addition 11 v1.0 alpha
    visible_posts = Post.objects.filter(
    Q(publish_time__isnull=True) | Q(publish_time__lte=timezone.now()),
    Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).order_by('-timestamp')

    # continue paginator setup
    paginator = Paginator(visible_posts.select_related('user__profile'), max_posts) # addition 11 v1.0 alpha

    page_number = request.GET.get('page', 1)
    current_page = paginator.get_page(page_number)

    # addition 12 v1.0 alpha
    post_data = []
    for post in current_page:
        personality = getattr(post.user.profile, 'personality', 'curious').lower()
        post_data.append({
            "post": post,
            "personality": personality,
        })

    return render(request, "network/index.html", {
        "current_page": current_page,
        "pagination": paginator.num_pages > 1,
        "post_data": post_data,  # addition 13 v1.0 alpha
    })



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


@login_required
def create_post(request):
    """ function that lets the use create a new post and handles error """

    if request.method == "POST":
        # get json data
        data = json.loads(request.body)
        content = data.get("content", "").strip()

        # check if content is valid
        if not content:
            print("Error: Cannot create an empty post.")
            return JsonResponse({"error": "Cannot create an empty post."}, status=400)

        post = Post(user=request.user, content=content)
        post.save()

        # getting the post in json format
        response_data = post.serialize()
        print("Post created successfully:", response_data)
        return JsonResponse(response_data, status=201)

    # else return error
    print("Error: Invalid request method")
    return JsonResponse({"error": "please use POST request"}, status=400)


@login_required
def profile_page(request, user_name):
    # get the current user and the viewed user's profile
    user_profile = get_object_or_404(User, username=user_name)
    current_user = request.user

    # conditional to check and confirm that the current signed in user cannot follow themselbves
    if request.method == 'POST' and current_user.is_authenticated and current_user != user_profile:
        if current_user.following.filter(id=user_profile.id).exists():
            current_user.following.remove(user_profile)
        else:
            current_user.following.add(user_profile)

        # redirect to the same profile page instead of doing json stuff
        return redirect('profile_page', user_name=user_name)

    # elif its a GET request then render the profile page, order the posts in reverse chrono order
    user_posts = Post.objects.filter(user=user_profile).order_by('-timestamp')
    is_own_profile = current_user == user_profile
    is_following = current_user.following.filter(id=user_profile.id).exists()

    return render(request, 'network/profile_page.html', {
        'user_profile': user_profile,
        'user_posts': user_posts,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'follower_count': user_profile.follower_count(),
        'following_count': user_profile.following_count(),
    })


@login_required
def following(request):
    """ function that shows the posts made by all the users the current user follows """

    # checking for, and filtering to show the current user's followed users posts. Using "__in" queryset built into django
    followed_users = User.objects.filter(followers=request.user)
    followed_posts = Post.objects.filter(user__in=followed_users).order_by('-timestamp')

    return render(request, "network/following.html", {
        # passing in the context for the template
        "posts": followed_posts,
    })


@login_required
def edit_post(request, post_id):
    """ function that allows the user to edit ONLY their own post but, nobody elses. """

    # getting the post object, else 404 not found (a new import from django.shortcuts)
    post = get_object_or_404(Post, id=post_id)

    # check if current user is author of post (a user cannot edit another user's posts)
    if post.user != request.user:
        return JsonResponse({"error": "Can't edit someone else's post."}, status=403)

    # get request to show post content fpr editing
    if request.method == "GET":
        return JsonResponse({"content": post.content})

    # handling POST request to edit the post (in JS/html part it must be prefilled)
    elif request.method == "POST":
        content = json.loads(request.body)
        new_content = content.get("content", "").strip()

        if not new_content:
            return JsonResponse({"error": "content of posts cannot be empty."}, status=400)

        # save new post and content therein
        post.content = new_content
        post.save()

        # return updated content via JSON and fetch api calls in template/script/html
        return JsonResponse({"content": post.content})


@login_required
def like_post(request, post_id):
    """ function that handles manipulation of all posts, to like/unlike them """

    if request.method == "POST":
        # filter post for the specific id
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)

        # toggle like status for posts
        if request.user in post.likes.all():
            # unlike
            post.likes.remove(request.user)
            liked = False
        else:
            # like
            post.likes.add(request.user)
            liked = True

        return JsonResponse({
            "message": "Success",
            "liked": liked,
            # updating like count for that post
            "likes": post.like_count(),
            "liked_by_user": liked
        })

    return JsonResponse({"error": "POST request required."}, status=400)
