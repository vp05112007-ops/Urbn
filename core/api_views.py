from django.http import JsonResponse
from .models import Product, Collection, Category

def get_products(request):
    try:
        products = Product.objects.filter(is_active=True)
        
        # Basic filtering (can expand later based on frontend query params)
        category = request.GET.get('category')
        if category and category != 'All Categories':
            products = products.filter(category__name=category)
            
        data = []
        for p in products:
            # Get unique sizes and colors from variants
            variants = p.variants.all()
            sizes = list(set([v.size for v in variants]))
            colors = list(set([v.color for v in variants]))
            
            badge = ''
            if p.is_new_arrival:
                badge = 'NEW'
            elif p.is_trending or p.is_featured:
                badge = 'BESTSELLER'
                
            data.append({
                'id': p.sku,
                'name': p.name,
                'category': p.category.name if p.category else '',
                'price': float(p.price),
                'image': p.primary_image_url or '/static/images/placeholder.png',
                'sizes': sizes,
                'colors': colors,
                'badge': badge,
                'date': p.created_at.strftime('%Y-%m-%d'),
                'db_id': p.id
            })
        return JsonResponse({'products': data})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

def get_collections(request):
    collections = Collection.objects.filter(is_active=True).order_by('display_order')
    data = []
    for c in collections:
        data.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description,
            'cover_image': c.cover_image.url if c.cover_image else None,
            'banner_image': c.banner_image.url if c.banner_image else None
        })
    return JsonResponse({'collections': data})
