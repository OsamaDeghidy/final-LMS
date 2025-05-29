from website.models import Category

def categories_processor(request):
    """
    Context processor that adds all categories to the template context.
    This makes the categories available in all templates.
    """
    return {
        'categories': Category.objects.all()
    }
