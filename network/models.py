# addition 9 v1.0 alpha
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    # can access followers using user.followers.all()
    following = models.ManyToManyField("self", related_name="followers", symmetrical=False)

    def follower_count(self):
         return User.objects.filter(following=self).count()

    def following_count(self):
        return self.following.count()

    def serialize(self):
        return {
            "follower_count": self.follower_count(),
            "following_count": self.following_count(),
            "id": self.id,
            "user": self.user.username
        }


class TarotCard(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='tarot_cards/', null=True, blank=True)  # optional

    def __str__(self):
        return self.name


class Post(models.Model):
    """ here we have post listings and its attributes for showing which posts belong to whom, who made the post, how many likes
    that post has """

    # id of post
    id = models.AutoField(primary_key=True)
    # can access the posts made by the current user by accessing the related_name field, by using user.posts.all()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    tarot_card = models.ForeignKey(
        TarotCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts"
    )

    # added 6 v1.0 alpha
    publish_time = models.DateTimeField(null=True, blank=True)

    # this will be the ManyToManyField with the User model to keep track of which users have liked a post
    likes = models.ManyToManyField(User, related_name="liked_posts")

    # Added 7 v1.0 alpha
    created = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # added 7 v1.0 alpha
    def update_expiry(self, likes, followers):
        base_life = timedelta(hours=24)
        extra_time = timedelta(hours=min(likes * 1.5, followers * 0.5))
        self.expires_at = self.created + base_life + extra_time
        self.save()

    def is_visible(self):
        return not self.publish_time or self.publish_time <= timezone.now()

    def like_count(self):
        return self.likes.count()


    # instantly turning the data into JSON for easier access in python and JS functions
    def serialize(self, user=None):
        return {
            "id": self.id,
            "user": self.user.username,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "likes": self.like_count(),
            "liked_by_user": user in self.likes.all() if user else False,
        }


# Addition 1 v1.0 alpha
class Profile(models.Model):
    PERSONALITY_CHOICES = [
        ('Bold', 'Bold'),
        ('Curious', 'Curious'),
        ('Melancholic', 'Melancholic'),
        ('Lively', 'Lively'),
        ('Mysterious', 'Mysterious'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    personality = models.CharField(max_length=20, choices=PERSONALITY_CHOICES, default='Curious')

    def __str__(self):
        return f"{self.user.username}'s Profile"
