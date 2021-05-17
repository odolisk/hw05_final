
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def get_paginator_page(request, posts):
    """Return pages from posts with POST_PER_PAGE (from settings)
    post on each."""
    paginator = Paginator(posts, settings.POST_PER_PAGE)
    num_pages = request.GET.get('page')
    return paginator.get_page(num_pages)


def index(request):
    """Return index page with last posts, ordered by date DESC."""
    all_posts = Post.objects.all()
    page = get_paginator_page(request, all_posts)
    return render(request, 'posts/index.html',
                  {'page': page})


def group_posts(request, slug):
    """Return page with last group posts, ordered by date DESC."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts_group.all()
    page = get_paginator_page(request, posts)
    return render(request, 'posts/group.html',
                  {'group': group, 'page': page})


@login_required
def new_post(request):
    """Add new post to site."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/edit.html',
                      {'form': form, 'post': None})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:index')


def follow_counts(request, username):
    """Return numbers of follows, numbers of following of usenamed author
    and status of follows by request user."""
    if request.user.is_authenticated:
        following = Follow.get_follow_or_none(request, username)
    else:
        following = False
    follow_val = Follow.objects.filter(
        user__username=username).count()
    following_val = Follow.objects.filter(
        author__username=username).count()
    return {'follow': follow_val,
            'following': following_val,
            'follow_flag': following
            }


def profile(request, username):
    """Return profile page with posts of 'username'."""
    author = get_object_or_404(User, username=username)
    posts = author.posts_author.all()
    page = get_paginator_page(request, posts)
    follow = follow_counts(request, username)
    return render(request, 'posts/profile.html',
                  {'page': page,
                   'author': author,
                   'follow': follow
                   })


def post_view(request, username, post_id):
    """Return post page with 'post_id' = post_id ."""
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    follow = follow_counts(request, username)
    return render(request, 'posts/post.html',
                  {'post': post,
                   'author': post.author,
                   'comments': comments,
                   'form': form,
                   'follow': follow,
                   })


@login_required
def post_edit(request, username, post_id):
    """Show form with the edited post and save valid post into db."""
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post',
                        username=username,
                        post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(request, 'posts/edit.html',
                      {'form': form, 'post': post})
    post = form.save()
    return redirect('posts:post',
                    username=request.user.username,
                    post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    """Add new comment to post with id = post_id."""
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    follow = follow_counts(request, username)
    if not form.is_valid():
        return render(request, 'posts/post.html',
                      {'post': post,
                       'author': post.author,
                       'comments': comments,
                       'form': form,
                       'follow': follow,
                       })
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    comments = post.comments.all()
    return redirect('posts:post',
                    username=username,
                    post_id=post_id)


@login_required
def follow_index(request):
    """Show posts of users which request user follow."""
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    page = get_paginator_page(request, posts)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    """Follow user with 'username' by 'request user'."""
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user.username)
    if author != user:
        if not (Follow.get_follow_or_none(request, username)):
            Follow.objects.create(
                author=author,
                user=user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Unfollow user with 'username' by 'request user'."""
    if Follow.get_follow_or_none(request, username):
        Follow.objects.get(
            author=get_object_or_404(User, username=username),
            user=get_object_or_404(
                User, username=request.user.username)).delete()
    return redirect('posts:profile', username=username)


def page_not_found(request, exception):
    """Return 404 error page."""
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=HTTPStatus.NOT_FOUND
    )


def server_error(request):
    """Return 500 error page."""
    return render(request, "misc/500.html",
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)


def forbidden(request):
    """Return 403 error page."""
    return render(request, 'misc/403.html', status=HTTPStatus.FORBIDDEN)
