from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment, Follow
from .utils import paginate_posts

User = get_user_model()


def index(request):
    posts_list = Post.objects.select_related('author', 'group')
    page_obj = paginate_posts(request, posts_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('author').all()
    context = {
        'group': group,
        'page_obj': paginate_posts(request, posts_list)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    )
        .exists()
    )
    context = {
        'author': author,
        'page_obj': paginate_posts(
            request, author.posts.select_related('group').all()
        ),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    queryset = (
        Post.objects
            .select_related('author', 'group')
            .prefetch_related('comments__author')
    )
    post = get_object_or_404(queryset, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'form': form, 'post': post, 'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", post.author.username)


@login_required
def post_edit(request, post_id):
    original_post = get_object_or_404(Post, pk=post_id)
    if request.user != original_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=original_post,
    )
    context = {"form": form}
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.author:
        comment.delete()
    return redirect('posts:post_detail', post_id=comment.post.id)

@login_required
def follow_index(request):
    posts_list = Post.objects.prefetch_related('author').filter(
        author__following__user=request.user
    )
    page_obj = paginate_posts(request, posts_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username
    ).delete()
    return redirect("posts:profile", username=username)
