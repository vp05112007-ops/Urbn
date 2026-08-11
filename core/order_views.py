from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import Order

@login_required
def my_orders(request):
    """
    List all orders for the authenticated user.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/my_orders.html', context)

@login_required
def order_details(request, order_number):
    """
    Detailed view of a single order. Ensures the order belongs to the user.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/order_details.html', context)

@login_required
def order_tracking(request, order_number):
    """
    Tracking timeline for a single order.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    history = order.status_history.all().order_by('created_at')
    
    # We will use this to determine the active step in the UI
    status_order = [
        ('PLACED', 'Placed'),
        ('PAYMENT_CONFIRMED', 'Payment Confirmed'),
        ('CONFIRMED', 'Confirmed'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered')
    ]
    
    current_step_index = -1
    for i, step in enumerate(status_order):
        if step[0] == order.order_status:
            current_step_index = i
            break
            
    context = {
        'order': order,
        'history': history,
        'status_order': status_order,
        'current_step_index': current_step_index,
    }
    return render(request, 'orders/order_tracking.html', context)

@login_required
def order_confirmation(request, order_number):
    """
    Success page shown after checkout.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_confirmed.html', context)

@login_required
def download_invoice(request, order_number):
    from .invoice import generate_invoice_pdf
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    pdf = generate_invoice_pdf(order)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="URBN-Invoice-{order_number}.pdf"'
    return response

@login_required
def resend_invoice(request, order_number):
    if request.method == 'POST':
        from .invoice import send_invoice_email
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Bypass idempotency check for manual resend
        order.invoice_sent = False
        success, msg = send_invoice_email(order, request=request)
        
        if success:
            messages.success(request, "Invoice successfully resent to your email.")
        else:
            messages.error(request, f"Failed to resend invoice: {msg}")
            
    return redirect('order_details', order_number=order_number)

from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from .models import OrderItem, ReturnRequest, ReturnRequestImage, ReturnRequestStatusHistory
from .returns import is_return_eligible, validate_return_image, send_return_status_email

@login_required
def create_return_request(request, order_number, item_id):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    eligible, check_data = is_return_eligible(order, order_item)
    
    if not eligible:
        messages.error(request, f"This item is not eligible for return: {check_data}")
        return redirect('order_details', order_number=order_number)
        
    available_qty = check_data.get('available_qty', 1)
    
    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '').strip()
        requested_quantity = int(request.POST.get('quantity', 1))
        
        exchange_size = request.POST.get('exchange_size')
        exchange_color = request.POST.get('exchange_color')
        
        images = request.FILES.getlist('images')
        
        # Validations
        if not reason or not description:
            messages.error(request, "Reason and problem statement are required.")
            return redirect('create_return_request', order_number=order.order_number, item_id=item_id)
            
        if requested_quantity > available_qty or requested_quantity < 1:
            messages.error(request, "Invalid quantity requested.")
            return redirect('create_return_request', order_number=order.order_number, item_id=item_id)
            
        if not images:
            messages.error(request, "Photographic evidence of the product is compulsory for all requests.")
            return redirect('create_return_request', order_number=order.order_number, item_id=item_id)
                
        if len(images) > 5:
            messages.error(request, "Maximum 5 images allowed.")
            return redirect('create_return_request', order_number=order.order_number, item_id=item_id)
            
        # Validate Images
        try:
            for image in images:
                validate_return_image(image)
        except ValidationError as e:
            messages.error(request, str(e.message))
            return redirect('create_return_request', order_number=order.order_number, item_id=item_id)
            
        # Create Request
        req_num = f"URBN-RET-{get_random_string(6).upper()}"
        
        return_req = ReturnRequest.objects.create(
            request_number=req_num,
            order=order,
            order_item=order_item,
            user=request.user,
            request_type=request_type,
            reason=reason,
            description=description,
            requested_quantity=requested_quantity,
            requested_exchange_size=exchange_size if request_type == 'EXCHANGE' else None,
            requested_exchange_color=exchange_color if request_type == 'EXCHANGE' else None
        )
        
        ReturnRequestStatusHistory.objects.create(
            return_request=return_req,
            status='REQUESTED',
            note='Return request submitted by customer.'
        )
        
        for image in images:
            ReturnRequestImage.objects.create(return_request=return_req, image=image)
            
        # Notify
        send_return_status_email(return_req, request=request)
        
        messages.success(request, f"Request {req_num} submitted successfully.")
        return redirect('return_requests_list')
        
    context = {
        'order': order,
        'item': order_item,
        'available_qty': available_qty,
        'qty_range': range(1, available_qty + 1),
    }
    return render(request, 'orders/return_request.html', context)

@login_required
def return_requests_list(request):
    requests = ReturnRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/return_requests_list.html', {'requests': requests})

@login_required
def return_request_detail(request, request_number):
    return_req = get_object_or_404(ReturnRequest, request_number=request_number, user=request.user)
    history = return_req.status_history.all()
    images = return_req.images.all()
    return render(request, 'orders/return_request_detail.html', {
        'return_req': return_req,
        'history': history,
        'images': images
    })
