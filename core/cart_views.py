import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem

# Authoritative Price Registry (since no Product model exists)
PRODUCT_PRICES = {
    'tr-1': Decimal('2499.00'), # Oversized Heavyweight Hoodie
    'tr-2': Decimal('1499.00'), # Boxy Fit Graphic T-Shirt
    'tr-3': Decimal('3299.00'), # Utility Cargo Pants
    'tr-4': Decimal('4999.00'), # Puffer Jacket
    'ct-1': Decimal('1999.00'), # Essential Hoodie
    'ct-2': Decimal('999.00'),  # Classic T-Shirt
    'ct-3': Decimal('2999.00'), # Windbreaker
    'ct-4': Decimal('2299.00'), # Sweatpants
    'ct-5': Decimal('1799.00'), # Sweatshirt
    'ct-6': Decimal('499.00'),  # Accessories
}

def get_authoritative_price(product_id, is_custom=False):
    if is_custom or str(product_id).startswith('custom-'):
        return Decimal('3499.00')
    return PRODUCT_PRICES.get(str(product_id), Decimal('1999.00')) # Fallback for now

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart

def _get_cart_data(request):
    cart = get_or_create_cart(request)
    items = []
    subtotal = Decimal('0.00')
    
    for item in cart.items.all().order_by('created_at'):
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'name': item.product_name,
            'quantity': item.quantity,
            'color': item.selected_color,
            'size': item.selected_size,
            'fit': item.selected_fit,
            'custom_text': item.custom_text,
            'placement': item.placement,
            'price': float(item.unit_price),
            'image': item.image_url,
        })
        subtotal += item.unit_price * item.quantity
        
    return {
        'items': items,
        'subtotal': float(subtotal),
        'count': sum(item['quantity'] for item in items)
    }

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_cart(request):
    return JsonResponse(_get_cart_data(request))

@require_http_methods(["POST"])
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID required'}, status=400)
            
        cart = get_or_create_cart(request)
        
        # Determine price authoritatively
        is_custom = str(product_id).startswith('custom-')
        unit_price = get_authoritative_price(product_id, is_custom)
        
        # Look for identical configuration
        custom_text = data.get('customText', '')
        if custom_text: custom_text = custom_text.strip()
        
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            selected_color=data.get('color', ''),
            selected_size=data.get('size', ''),
            selected_fit=data.get('fit', ''),
            custom_text=custom_text,
            placement=data.get('placement', ''),
            defaults={
                'product_name': data.get('name', 'Unknown Product'),
                'unit_price': unit_price,
                'quantity': data.get('quantity', 1),
                'image_url': data.get('image', '')
            }
        )
        
        if not created:
            new_qty = item.quantity + int(data.get('quantity', 1))
            item.quantity = max(1, min(9, new_qty))
            item.save()
        else:
            item.quantity = max(1, min(9, item.quantity))
            item.save()
            
        return JsonResponse(_get_cart_data(request))
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["PATCH"])
def update_cart_item(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 0))
        
        cart = get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity > 0:
            item.quantity = max(1, min(9, quantity))
            item.save()
        else:
            item.delete()
            
        return JsonResponse(_get_cart_data(request))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["DELETE"])
def remove_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return JsonResponse(_get_cart_data(request))
