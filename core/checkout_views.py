import json
import os
import uuid
import hmac
import hashlib
from datetime import datetime
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, Address

# Get credentials from env
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

def get_razorpay_client():
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    return None

@login_required
def checkout_page(request):
    try:
        cart = Cart.objects.get(user=request.user)
        items = cart.items.all()
    except Cart.DoesNotExist:
        items = []

    if not items:
        # Cannot checkout an empty bag
        return redirect('home')

    # Calculate totals securely on server
    subtotal = sum((item.unit_price * item.quantity for item in items), Decimal('0.00'))
    shipping_charge = Decimal('0.00')  # Free shipping MVP
    discount = Decimal('0.00')
    total_amount = subtotal + shipping_charge - discount

    # Prefill address
    default_address = request.user.addresses.filter(is_default=True).first()
    if not default_address:
        default_address = request.user.addresses.first()

    context = {
        'items': items,
        'subtotal': subtotal,
        'shipping_charge': shipping_charge,
        'discount': discount,
        'total_amount': total_amount,
        'default_address': default_address,
        'razorpay_key_id': RAZORPAY_KEY_ID, # Expose only public key
    }
    return render(request, 'checkout/checkout.html', context)


@login_required
@transaction.atomic
def create_razorpay_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        
        # Get cart
        cart = Cart.objects.get(user=request.user)
        items = list(cart.items.all())
        
        if not items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
            
        # Inventory / Stock Check
        for item in items:
            if hasattr(item, 'product') and item.product:
                if item.quantity > item.product.stock_quantity:
                    return JsonResponse({
                        'error': f'Not enough stock for {item.product.name}. Available: {item.product.stock_quantity}'
                    }, status=400)

        # Re-calculate totals on the backend
        subtotal = sum((item.unit_price * item.quantity for item in items), Decimal('0.00'))
        shipping_charge = Decimal('0.00')
        discount = Decimal('0.00')
        total_amount = subtotal + shipping_charge - discount

        # Generate unique order number
        date_str = datetime.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:4].upper()
        order_number = f"URBN-{date_str}-{unique_id}"

        # Fallback to default address if frontend doesn't supply it
        address = request.user.addresses.filter(is_default=True).first()
        if not address:
            address = request.user.addresses.first()

        first_name = data.get('first_name') or (address.full_name.split()[0] if address else request.user.first_name)
        last_name = data.get('last_name') or (' '.join(address.full_name.split()[1:]) if address and len(address.full_name.split()) > 1 else request.user.last_name)
        phone = data.get('phone') or (address.phone if address else (request.user.profile.phone if hasattr(request.user, 'profile') else ''))
        
        # Create Pending Order
        order = Order.objects.create(
            order_number=order_number,
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=data.get('email', request.user.email),
            phone=phone,
            address_line_1=data.get('address_line_1') or (address.address_line_1 if address else ''),
            address_line_2=data.get('address_line_2') or (address.address_line_2 if address else ''),
            city=data.get('city') or (address.city if address else ''),
            state=data.get('state') or (address.state if address else ''),
            country=data.get('country') or (address.country if address else ''),
            pincode=data.get('pincode') or (address.postal_code if address else ''),
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            discount=discount,
            total_amount=total_amount,
            payment_status='PENDING',
            order_status='PLACED'
        )

        OrderStatusHistory.objects.create(
            order=order,
            status='PLACED',
            message='Order placed, awaiting payment.'
        )

        # Create Order Items (Snapshots)
        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item.product_id,
                product_name_snapshot=item.product_name,
                product_image_snapshot=item.image_url,
                unit_price=item.unit_price,
                size=item.selected_size,
                color=item.selected_color,
                quantity=item.quantity,
                custom_text=item.custom_text,
                placement=item.placement,
                subtotal=item.unit_price * item.quantity
            )

        # Create Razorpay Order
        client = get_razorpay_client()
        if not client:
            return JsonResponse({'error': 'Payment gateway not configured'}, status=500)

        # Amount in paise
        amount_in_paise = int(total_amount * 100)
        
        razorpay_order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order_number,
            "notes": {
                "order_id": str(order.id)
            }
        }
        
        razorpay_order = client.order.create(data=razorpay_order_data)
        
        # Save razorpay order ID to our DB order
        order.razorpay_order_id = razorpay_order['id']
        order.save()

        return JsonResponse({
            'success': True,
            'key_id': RAZORPAY_KEY_ID,
            'order_id': order.id,
            'order_number': order_number,
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'customer_name': f"{order.first_name} {order.last_name}",
            'customer_email': order.email,
            'customer_phone': order.phone,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@transaction.atomic
def payment_success(request):
    """
    Called by frontend after Razorpay checkout JS succeeds.
    We must verify the signature server-side before trusting it.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        local_order_id = data.get('local_order_id')

        # 1. Get the local order and ensure it matches the Razorpay Order ID passed
        order = get_object_or_404(Order, id=local_order_id, user=request.user)
        
        if order.razorpay_order_id != razorpay_order_id:
            return JsonResponse({'error': 'Order ID mismatch'}, status=400)
            
        if order.payment_status == 'PAID':
            return JsonResponse({'success': True, 'message': 'Already paid'})

        # 2. Verify signature server-side
        client = get_razorpay_client()
        if not client:
            return JsonResponse({'error': 'Payment gateway not configured'}, status=500)
            
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'error': 'Payment verification failed'}, status=400)

        # 3. Mark as paid
        order.payment_status = 'PAID'
        order.order_status = 'PAYMENT_CONFIRMED'
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.save()

        OrderStatusHistory.objects.create(
            order=order,
            status='PAYMENT_CONFIRMED',
            message='Payment verified and confirmed.'
        )

        # 4. Reduce stock quantity
        for item in order.items.all():
            product = getattr(item, 'product', None)
            if product:
                product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                product.save()

        # 5. Clear the cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass

        # 5. Send Invoice Email (Idempotent and Fail-Safe)
        try:
            from core.invoice import send_invoice_email
            if not order.invoice_sent:
                send_invoice_email(order, request=request)
        except Exception as e:
            # Don't fail the order if email fails
            print(f"Failed to send invoice email: {e}")

        return JsonResponse({'success': True, 'order_number': order.order_number})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def razorpay_webhook(request):
    """
    Idempotent webhook to handle Razorpay events reliably.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    webhook_signature = request.headers.get('X-Razorpay-Signature')
    if not webhook_signature:
        return HttpResponse(status=400)

    try:
        body = request.body.decode('utf-8')
        
        # Verify Webhook signature
        client = get_razorpay_client()
        if not client:
            return HttpResponse(status=500)

        try:
            client.utility.verify_webhook_signature(body, webhook_signature, RAZORPAY_WEBHOOK_SECRET)
        except razorpay.errors.SignatureVerificationError:
            return HttpResponse(status=400)

        event = json.loads(body)
        
        # Handle payment.captured
        if event['event'] == 'payment.captured':
            payment = event['payload']['payment']['entity']
            razorpay_order_id = payment.get('order_id')
            razorpay_payment_id = payment.get('id')
            
            if razorpay_order_id:
                try:
                    with transaction.atomic():
                        order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                        
                        # Idempotency check
                        if order.payment_status != 'PAID':
                            order.payment_status = 'PAID'
                            order.order_status = 'PAYMENT_CONFIRMED'
                            order.razorpay_payment_id = razorpay_payment_id
                            order.save()
                            
                            OrderStatusHistory.objects.create(
                                order=order,
                                status='PAYMENT_CONFIRMED',
                                message='Payment captured via webhook.'
                            )
                            
                            # Reduce stock quantity
                            for item in order.items.all():
                                product = getattr(item, 'product', None)
                                if product:
                                    product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                                    product.save()
                            
                            # Also clear cart if it exists (using user)
                            cart = Cart.objects.filter(user=order.user).first()
                            if cart:
                                cart.items.all().delete()
                                
                            # Send email if it hasn't been sent yet
                            subject = f"URBN — Order Confirmed {order.order_number}"
                            message = f"Hello {order.first_name},\n\nYour URBN order has been confirmed.\nOrder Number: {order.order_number}\nTotal: ₹{order.total_amount}\n\nThank you for shopping with us!"
                            send_mail(
                                subject,
                                message,
                                settings.DEFAULT_FROM_EMAIL,
                                [order.email],
                                fail_silently=True,
                            )
                except Order.DoesNotExist:
                    pass

        return HttpResponse(status=200)

    except Exception as e:
        return HttpResponse(status=500)
