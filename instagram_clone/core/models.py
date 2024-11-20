from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils.safestring import mark_safe

class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics', default='default.jpg')
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_stats(self):
        return {
            'posts_count': self.posts.count(),
            'followers_count': self.followers.count(),
            'following_count': self.following.count(),
            'comments_count': self.comments.count(),
            'likes_given_count': self.liked_posts.count(),
            'likes_received_count': sum(post.likes.count() for post in self.posts.all()),
            'total_hashtags': sum(post.hashtags.count() for post in self.posts.all()),
        }

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='posts')
    caption = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts')
    hashtags = models.ManyToManyField('Hashtag', related_name='posts')
    
    class Meta:
        ordering = ['-created_at']
    
    def get_likes_count(self):
        return self.likes.count()

    def get_caption_with_hashtags(self):
        # Process caption and format hashtags as HTML links
        words = self.caption.split()
        seen_hashtags = set()
        result = []
        
        for word in words:
            if word.startswith('#'):
                tag = word.lower()
                if tag not in seen_hashtags:
                    seen_hashtags.add(tag)
                    result.append(f'<a href="/tag/{word[1:]}/" class="hashtag">{word}</a>')
            else:
                result.append(word)
        
        return mark_safe(' '.join(result))

    def get_hashtags_display(self):
        # Format hashtags with # prefix
        return [f"#{tag.name}" for tag in self.hashtags.all()]

    def get_hashtags(self):
        return self.hashtags.distinct()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    def save(self, *args, **kwargs):
        # Process and save hashtags from caption
        super().save(*args, **kwargs)
        
        self.hashtags.clear()
        
        hashtags = set()
        for word in self.caption.split():
            if word.startswith('#'):
                tag_name = word[1:]
                if tag_name:
                    hashtags.add(tag_name.lower())
        
        for tag_name in hashtags:
            hashtag, _ = Hashtag.objects.get_or_create(name=tag_name)
            self.hashtags.add(hashtag)
