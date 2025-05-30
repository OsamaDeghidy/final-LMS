from django.urls import path
from . import views_article

# Article URLs
urlpatterns = [
    path('articles/', views_article.article_list, name='article_list'),
    path('articles/create/', views_article.create_article, name='create_article'),
    path('articles/category/<int:category_id>/', views_article.articles_by_category, name='articles_by_category'),
    path('articles/tag/<int:tag_id>/', views_article.articles_by_tag, name='articles_by_tag'),
    path('my-articles/', views_article.my_articles, name='my_articles'),
    path('articles/<slug:slug>/update/', views_article.update_article, name='update_article'),
    path('articles/<slug:slug>/delete/', views_article.delete_article, name='delete_article'),
    path('articles/<slug:slug>/', views_article.article_detail, name='article_detail'),
]
