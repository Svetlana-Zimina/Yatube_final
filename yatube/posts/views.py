from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from posts.utils import get_page_obj
from posts.forms import CommentForm, PostForm
from posts.models import (
    Follow,
    Group,
    Post,
    User
)


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    context = {
        'page_obj': get_page_obj(posts, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_page_obj(group_posts, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()
        context = {
            'author': author,
            'page_obj': get_page_obj(posts, request),
            'following': following
        }
        return render(request, 'posts/profile.html', context)
    else:
        context = {
            'author': author,
            'page_obj': get_page_obj(posts, request),
        }
        return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:profile', post.author)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/post_create.html',
                  {'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': get_page_obj(post_list, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    following_author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        author=following_author,
        user=request.user
    ).exists()
    if request.user != following_author and following is False:
        Follow.objects.create(
            author=following_author,
            user=request.user
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following_author = get_object_or_404(User, username=username)
    if Follow.objects.filter(
        author=following_author,
        user=request.user
    ).exists():
        Follow.objects.filter(author=following_author).delete()
    return redirect('posts:profile', username=username)
