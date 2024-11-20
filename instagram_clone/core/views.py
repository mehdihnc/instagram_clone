from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.template.defaultfilters import slugify
from .models import User, Post, Comment, Hashtag
from .forms import UserRegisterForm, UserUpdateForm, PostForm, CommentForm, EmailAuthenticationForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé avec succès pour {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def feed(request):
    following_users = request.user.following.all()
    posts = Post.objects.filter(user__in=following_users).select_related('user').prefetch_related('comments', 'likes')
    return render(request, 'core/feed.html', {'posts': posts})

@login_required
def explore(request):
    posts = Post.objects.all().order_by('-created_at').select_related('user')
    return render(request, 'core/explore.html', {'posts': posts})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            
            # Traitement des hashtags
            caption = form.cleaned_data['caption']
            words = caption.split()
            hashtags = set(word[1:] for word in words if word.startswith('#'))
            
            for tag_name in hashtags:
                original_tag = tag_name
                tag_name = ''.join(c for c in tag_name if c.isalnum())
                if tag_name:
                    hashtag, created = Hashtag.objects.get_or_create(
                        name__iexact=tag_name,
                        defaults={'name': original_tag, 'slug': slugify(tag_name)}
                    )
                    post.hashtags.add(hashtag)
            
            messages.success(request, 'Post créé avec succès!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm()
    return render(request, 'core/create_post.html', {'form': form})

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user').prefetch_related('comments__user', 'likes'), id=post_id)
    post.cleaned_content = clean_content(post.caption)
    comment_form = CommentForm()
    return render(request, 'core/post_detail.html', {'post': post, 'comment_form': comment_form})

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user).order_by('-created_at')
    is_following = request.user.following.filter(id=user.id).exists()
    
    context = {
        'profile_user': user,
        'posts': posts,
        'is_following': is_following,
        'posts_count': posts.count(),
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
    }
    return render(request, 'core/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'core/edit_profile.html', {
        'form': form,
        'user': request.user
    })

# Vues AJAX
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'likes_count': post.likes.count(), 'liked': liked})

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if request.user != user_to_follow:
        if request.user in user_to_follow.followers.all():
            user_to_follow.followers.remove(request.user)
            is_following = False
        else:
            user_to_follow.followers.add(request.user)
            is_following = True
        return JsonResponse({'status': 'ok', 'following': is_following})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return JsonResponse({
                'status': 'success',
                'comment_id': comment.id,
                'username': comment.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%d %b %Y')
            })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def hashtag_posts(request, tag_name):
    hashtag = get_object_or_404(Hashtag, name__iexact=tag_name)
    posts = Post.objects.filter(hashtags=hashtag).order_by('-created_at')
    return render(request, 'core/hashtag_posts.html', {
        'hashtag': hashtag,
        'posts': posts,
        'posts_count': posts.count()
    })

def process_hashtags(text):
    """Fonction utilitaire pour convertir les hashtags en liens cliquables"""
    words = text.split()
    for i, word in enumerate(words):
        if word.startswith('#'):
            tag = word[1:]
            if tag:  # Vérifie que le tag n'est pas vide
                words[i] = f'<a href="/tag/{tag}/" class="hashtag">#{tag}</a>'
    return ' '.join(words)

@login_required
def search_hashtags(request):
    query = request.GET.get('q', '').strip('#')
    if query:
        hashtags = Hashtag.objects.filter(name__icontains=query)
        posts = Post.objects.filter(hashtags__name__icontains=query).distinct()
    else:
        hashtags = []
        posts = []
    
    return render(request, 'core/search_hashtags.html', {
        'query': query,
        'hashtags': hashtags,
        'posts': posts
    })

def clean_content(content):
    # Retourne le texte sans les hashtags
    return ' '.join(word for word in content.split() if not word.startswith('#'))

def logout_view(request):
    logout(request)
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('feed')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def account_settings(request):
    user_stats = request.user.get_stats()
    return render(request, 'core/account_settings.html', {
        'user': request.user,
        'user_stats': user_stats
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        if user.check_password(password):
            # Déconnexion de l'utilisateur
            logout(request)
            # Suppression du compte
            user.delete()
            messages.success(request, 'Votre compte a été supprimé avec succès.')
            return redirect('login')
        else:
            messages.error(request, 'Mot de passe incorrect.')
    return render(request, 'core/delete_account.html')
