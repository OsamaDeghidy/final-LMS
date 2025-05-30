from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.utils.text import slugify

from .models import Article, Category, Tags
from user.models import Profile, Student, Teacher

def article_list(request):
    """
    Display a list of all published articles with filtering and pagination
    """
    # Get all published articles
    articles = Article.objects.filter(status='published').order_by('-created_at')
    
    # Get filter parameters
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    search_query = request.GET.get('q')
    
    # Apply filters if provided
    if category_id:
        articles = articles.filter(category_id=category_id)
    
    if tag_id:
        articles = articles.filter(tags__id=tag_id)
    
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(summary__icontains=search_query)
        )
    
    # Featured articles
    featured_articles = Article.objects.filter(featured=True, status='published').order_by('-created_at')[:3]
    
    # Pagination
    paginator = Paginator(articles, 9)  # Show 9 articles per page
    page = request.GET.get('page')
    
    try:
        articles_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        articles_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        articles_page = paginator.page(paginator.num_pages)
    
    # Get all categories and tags for filtering
    categories = Category.objects.all()
    tags = Tags.objects.all()
    
    context = {
        'articles': articles_page,
        'featured_articles': featured_articles,
        'categories': categories,
        'tags': tags,
        'current_category': category_id,
        'current_tag': tag_id,
        'search_query': search_query,
    }
    
    return render(request, 'website/articles/article_list.html', context)

def article_detail(request, slug):
    """
    Display a single article
    """
    article = get_object_or_404(Article, slug=slug)
    
    # Increment view count
    article.increment_views()
    
    # Get related articles (same category or tags)
    related_articles = Article.objects.filter(
        status='published'
    ).exclude(id=article.id)
    
    if article.category:
        related_articles = related_articles.filter(category=article.category)
    
    related_articles = related_articles[:3]  # Limit to 3 related articles
    
    # Get all categories for sidebar
    categories = Category.objects.all()
    
    # Get popular articles
    popular_articles = Article.objects.filter(
        status='published'
    ).order_by('-views_count')[:5]
    
    context = {
        'article': article,
        'related_articles': related_articles,
        'categories': categories,
        'popular_articles': popular_articles,
    }
    
    return render(request, 'website/articles/article_detail.html', context)

def articles_by_category(request, category_id):
    """
    Display articles filtered by category
    """
    category = get_object_or_404(Category, id=category_id)
    return article_list(request)

def articles_by_tag(request, tag_id):
    """
    Display articles filtered by tag
    """
    tag = get_object_or_404(Tags, id=tag_id)
    return article_list(request)

@login_required
def my_articles(request):
    """
    Display articles created by the current user
    """
    articles = Article.objects.filter(author=request.user).order_by('-created_at')
    
    # Get user profile data for dashboard template
    profile = Profile.objects.get(user=request.user)
    
    # Get student or teacher data if available
    student = None
    teacher = None
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        pass
    
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        pass
    
    context = {
        'articles': articles,
        'profile': profile,
        'student': student,
        'teacher': teacher,
    }
    
    return render(request, 'website/articles/my_articles.html', context)

@login_required
def create_article(request):
    """
    Create a new article
    """
    # Get user profile data for dashboard template
    profile = Profile.objects.get(user=request.user)
    
    # Get student or teacher data if available
    student = None
    teacher = None
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        pass
    
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        pass
        
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        summary = request.POST.get('summary')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        status = request.POST.get('status', 'draft')
        featured = request.POST.get('featured') == 'on'
        image = request.FILES.get('image')
        
        if not title or not content:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
            return redirect('create_article')
        
        # Create new article
        article = Article(
            title=title,
            content=content,
            summary=summary,
            author=request.user,
            status=status,
            featured=featured
        )
        
        # Set category if provided
        if category_id:
            article.category = get_object_or_404(Category, id=category_id)
        
        # Set image if provided
        if image:
            article.image = image
        
        # Save article to generate slug
        article.save()
        
        # Add tags
        if tag_ids:
            article.tags.set(tag_ids)
        
        messages.success(request, 'تم إنشاء المقالة بنجاح')
        return redirect('article_detail', slug=article.slug)
    
    # GET request - show form
    categories = Category.objects.all()
    tags = Tags.objects.all()
    
    context = {
        'categories': categories,
        'tags': tags,
        'profile': profile,
        'student': student,
        'teacher': teacher,
    }
    
    return render(request, 'website/articles/create_article.html', context)

@login_required
def update_article(request, slug):
    """
    Update an existing article
    """
    article = get_object_or_404(Article, slug=slug)
    
    # Get user profile data for dashboard template
    profile = Profile.objects.get(user=request.user)
    
    # Get student or teacher data if available
    student = None
    teacher = None
    try:
        student = Student.objects.get(profile__user=request.user)
    except Student.DoesNotExist:
        pass
    
    try:
        teacher = Teacher.objects.get(profile__user=request.user)
    except Teacher.DoesNotExist:
        pass
    
    # Check if user is the author
    if article.author != request.user and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لتعديل هذه المقالة')
        return redirect('article_detail', slug=article.slug)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        summary = request.POST.get('summary')
        category_id = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        status = request.POST.get('status', 'draft')
        featured = request.POST.get('featured') == 'on'
        image = request.FILES.get('image')
        
        if not title or not content:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
            return redirect('update_article', slug=article.slug)
        
        # Update article fields
        article.title = title
        article.content = content
        article.summary = summary
        article.status = status
        article.featured = featured
        
        # Update slug only if title changed
        if title != article.title:
            base_slug = slugify(title)
            unique_slug = base_slug
            num = 1
            while Article.objects.filter(slug=unique_slug).exclude(id=article.id).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            article.slug = unique_slug
        
        # Set category if provided
        if category_id:
            article.category = get_object_or_404(Category, id=category_id)
        else:
            article.category = None
        
        # Set image if provided
        if image:
            article.image = image
        
        # Save article
        article.save()
        
        # Update tags
        article.tags.clear()
        if tag_ids:
            article.tags.set(tag_ids)
        
        messages.success(request, 'تم تحديث المقالة بنجاح')
        return redirect('article_detail', slug=article.slug)
    
    # GET request - show form with article data
    categories = Category.objects.all()
    tags = Tags.objects.all()
    
    context = {
        'article': article,
        'categories': categories,
        'tags': tags,
        'profile': profile,
        'student': student,
        'teacher': teacher,
    }
    
    return render(request, 'website/articles/update_article.html', context)

@login_required
@require_POST
def delete_article(request, slug):
    """
    Delete an article
    """
    article = get_object_or_404(Article, slug=slug)
    
    # Check if user is the author
    if article.author != request.user and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لحذف هذه المقالة')
        return redirect('article_detail', slug=article.slug)
    
    # Delete article
    article.delete()
    
    messages.success(request, 'تم حذف المقالة بنجاح')
    return redirect('my_articles')
