from django.shortcuts import render, redirect, get_object_or_404
from .decorators import urbn_admin_required
from django.contrib import messages
from .models import Order, Product, Category, Collection, Refund, ReturnRequest, ProductVariant, StoreSettings, OrderStatusHistory, ReturnRequestStatusHistory
from django.db.models import Sum

@urbn_admin_required
def dashboard_home(request):
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status='PLACED').count()
    
    # Calculate revenue manually or via aggregate
    revenue_agg = Order.objects.filter(payment_status='PAID').aggregate(Sum('total_amount'))
    total_revenue = revenue_agg['total_amount__sum'] or 0
    
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

@urbn_admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Optional filtering
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
        
    payment = request.GET.get('payment')
    if payment:
        orders = orders.filter(payment_status=payment)
        
    return render(request, 'admin_dashboard/orders.html', {'orders': orders})

@urbn_admin_required
def admin_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment = request.POST.get('payment_status')
        tracking_number = request.POST.get('tracking_number')
        
        updated = False
        if new_status and new_status != order.order_status:
            order.order_status = new_status
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                message=f"Status updated to {dict(Order.STATUS_CHOICES).get(new_status, new_status)} by admin."
            )
            updated = True
        if new_payment and new_payment != order.payment_status:
            order.payment_status = new_payment
            updated = True
        if tracking_number is not None and tracking_number != order.tracking_number:
            order.tracking_number = tracking_number
            updated = True
            
        if updated:
            order.save()
            messages.success(request, f"Order {order.order_number} updated successfully.")
            return redirect('admin_order_detail', order_number=order.order_number)
            
    return render(request, 'admin_dashboard/order_detail.html', {'order': order})

@urbn_admin_required
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
        
    return render(request, 'admin_dashboard/products.html', {
        'products': products,
        'categories': Category.objects.all()
    })

@urbn_admin_required
def admin_product_edit(request, sku):
    product = get_object_or_404(Product, sku=sku)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.is_active = request.POST.get('is_active') == 'on'
        product.is_trending = request.POST.get('is_trending') == 'on'
        product.is_new_arrival = request.POST.get('is_new_arrival') == 'on'
        
        category_id = request.POST.get('category')
        if category_id:
            product.category_id = category_id
            
        product.save()
        messages.success(request, f"Product {product.sku} updated successfully.")
        return redirect('admin_products')
        
    return render(request, 'admin_dashboard/product_edit.html', {
        'product': product,
        'categories': Category.objects.all()
    })

@urbn_admin_required
def admin_categories(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'admin_dashboard/categories.html', {'categories': categories})

@urbn_admin_required
def admin_collections(request):
    collections = Collection.objects.all().order_by('display_order')
    return render(request, 'admin_dashboard/collections.html', {'collections': collections})

@urbn_admin_required
def admin_returns(request):
    returns = ReturnRequest.objects.all().order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        returns = returns.filter(status=status)
        
    return render(request, 'admin_dashboard/returns.html', {'returns': returns})

from django.utils import timezone
from core.returns import send_return_status_email

@urbn_admin_required
def admin_return_detail(request, request_number):
    return_req = get_object_or_404(ReturnRequest.objects.select_related('order', 'order_item', 'user', 'refund').prefetch_related('images', 'status_history'), request_number=request_number)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'APPROVE':
            return_req.status = 'APPROVED'
            return_req.approved_at = timezone.now()
            return_req.save()
            ReturnRequestStatusHistory.objects.create(
                return_request=return_req,
                status='APPROVED',
                note='Request approved by admin.',
                changed_by=request.user
            )
            send_return_status_email(return_req, request=request)
            messages.success(request, f"Request {return_req.request_number} approved.")
            
        elif action == 'REJECT':
            reason = request.POST.get('rejection_reason', '').strip()
            if not reason:
                messages.error(request, "Rejection reason is required.")
            else:
                return_req.status = 'REJECTED'
                return_req.rejection_reason = reason
                return_req.save()
                ReturnRequestStatusHistory.objects.create(
                    return_request=return_req,
                    status='REJECTED',
                    note=f'Rejected by admin. Reason: {reason}',
                    changed_by=request.user
                )
                send_return_status_email(return_req, request=request)
                messages.success(request, f"Request {return_req.request_number} rejected.")
                
        elif action == 'UPDATE_STATUS':
            new_status = request.POST.get('status')
            if new_status and new_status != return_req.status:
                return_req.status = new_status
                return_req.save()
                ReturnRequestStatusHistory.objects.create(
                    return_request=return_req,
                    status=new_status,
                    note='Status manually updated by admin.',
                    changed_by=request.user
                )
                messages.success(request, f"Return {return_req.request_number} status updated to {new_status}.")
                
        elif action == 'SAVE_NOTE':
            note = request.POST.get('admin_notes', '')
            return_req.admin_notes = note
            return_req.save()
            messages.success(request, "Admin notes saved.")
            
        return redirect('admin_return_detail', request_number=return_req.request_number)
            
    context = {
        'return_req': return_req,
        'status_choices': ReturnRequest.STATUS_CHOICES
    }
    return render(request, 'admin_dashboard/return_detail.html', context)

import razorpay
from django.conf import settings
from django.contrib.auth.models import User

@urbn_admin_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_dashboard/users.html', {'users': users})

@urbn_admin_required
def admin_process_refund(request, request_number):
    if request.method == 'POST':
        return_req = get_object_or_404(ReturnRequest, request_number=request_number)
        
        # Security checks
        if return_req.request_type != 'RETURN':
            messages.error(request, "Only RETURN requests can be refunded.")
            return redirect('admin_return_detail', request_number=return_req.request_number)
            
        if return_req.status != 'APPROVED':
            messages.error(request, "Return request must be APPROVED before processing refund.")
            return redirect('admin_return_detail', request_number=return_req.request_number)
            
        order = return_req.order
        if order.payment_status == 'REFUNDED':
            messages.error(request, "This order has already been marked as refunded.")
            return redirect('admin_return_detail', request_number=return_req.request_number)
            
        if not order.razorpay_payment_id:
            messages.error(request, "No Razorpay Payment ID found for this order. Manual refund required.")
            return redirect('admin_return_detail', request_number=return_req.request_number)
            
        # Refund Amount = unit_price * requested_quantity
        refund_amount = return_req.order_item.unit_price * return_req.requested_quantity
        
        try:
            import os
            key_id = os.environ.get('RAZORPAY_KEY_ID', '')
            key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
            client = razorpay.Client(auth=(key_id, key_secret))
            refund_data = {
                'amount': int(refund_amount * 100), # Amount in paise
                'receipt': return_req.request_number
            }
            
            refund = client.payment.refund(order.razorpay_payment_id, refund_data)
            
            # Save Refund object for records
            Refund.objects.create(
                order=order,
                return_request=return_req,
                amount=refund_amount,
                razorpay_refund_id=refund.get('id'),
                status='COMPLETED'
            )
            
            # Update Return Request Status
            return_req.status = 'REFUND_PROCESSING' # or COMPLETED based on existing model? Let's use COMPLETED as per prompt flow: "○ Refund Processing -> ○ Completed"
            return_req.completed_at = timezone.now()
            return_req.save()
            
            ReturnRequestStatusHistory.objects.create(
                return_request=return_req,
                status='COMPLETED',
                note=f'Refund of ₹{refund_amount} processed via Razorpay. Refund ID: {refund.get("id")}',
                changed_by=request.user
            )
            
            # Send customer email (assuming template supports status COMPLETED or we can just trigger it)
            send_return_status_email(return_req, request=request)
            
            # Update Order Status if all items returned (simplification: we just update it if any refund happens, but maybe not)
            order.payment_status = 'REFUNDED'
            order.status = 'CANCELLED'
            order.save()
            
            messages.success(request, f"Successfully refunded ₹{refund_amount} via Razorpay. Refund ID: {refund.get('id')}")
            
        except razorpay.errors.BadRequestError as e:
            messages.error(request, f"Razorpay Bad Request: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error processing refund: {str(e)}")
        
    return redirect('admin_return_detail', request_number=request_number)

@urbn_admin_required
def admin_inventory(request):
    if request.method == 'POST':
        try:
            variant_id = request.POST.get('variant_id')
            new_stock = int(request.POST.get('stock', 0))
            if new_stock < 0:
                messages.error(request, "Stock cannot be negative.")
            else:
                variant = get_object_or_404(ProductVariant, id=variant_id)
                variant.stock = new_stock
                variant.save()
                messages.success(request, f"Stock updated for {variant.product.name} ({variant.size}/{variant.color})")
        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")
        return redirect('admin_inventory')
        
    settings = StoreSettings.load()
    variants = ProductVariant.objects.select_related('product', 'product__category').all().order_by('product__name', 'size', 'color')
    
    from django.db.models import F
    total_products = Product.objects.count()
    in_stock_count = ProductVariant.objects.filter(stock__gt=F('reserved_stock') + settings.low_stock_threshold).count()
    low_stock_count = ProductVariant.objects.filter(stock__lte=F('reserved_stock') + settings.low_stock_threshold, stock__gt=F('reserved_stock')).count()
    out_of_stock_count = ProductVariant.objects.filter(stock__lte=F('reserved_stock')).count()
    
    # Simple search/filter
    q = request.GET.get('q')
    if q:
        variants = variants.filter(product__name__icontains=q) | variants.filter(product__sku__icontains=q)
        
    filter_val = request.GET.get('filter')
    if filter_val == 'instock':
        variants = variants.filter(stock__gt=F('reserved_stock') + settings.low_stock_threshold)
    elif filter_val == 'lowstock':
        variants = variants.filter(stock__lte=F('reserved_stock') + settings.low_stock_threshold, stock__gt=F('reserved_stock'))
    elif filter_val == 'outofstock':
        variants = variants.filter(stock__lte=F('reserved_stock'))
        
    context = {
        'variants': variants,
        'settings': settings,
        'total_products': total_products,
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'current_filter': filter_val,
    }
    return render(request, 'admin_dashboard/inventory.html', context)

@urbn_admin_required
def admin_refunds(request):
    refunds = Refund.objects.select_related('order', 'return_request').all().order_by('-created_at')
    
    q = request.GET.get('q')
    if q:
        refunds = refunds.filter(order__order_number__icontains=q) | refunds.filter(order__user__email__icontains=q)
        
    filter_val = request.GET.get('filter')
    if filter_val and filter_val != 'all':
        refunds = refunds.filter(status=filter_val.upper())

    pending_review = Refund.objects.filter(status__in=['REFUND_REQUESTED', 'UNDER_REVIEW']).count()
    approved = Refund.objects.filter(status='APPROVED').count()
    processing = Refund.objects.filter(status='PROCESSING').count()
    completed = Refund.objects.filter(status='PROCESSED').count()

    context = {
        'refunds': refunds,
        'pending_review': pending_review,
        'approved': approved,
        'processing': processing,
        'completed': completed,
        'current_filter': filter_val
    }
    return render(request, 'admin_dashboard/refunds.html', context)

@urbn_admin_required
def admin_refund_detail(request, refund_id):
    refund = get_object_or_404(Refund, id=refund_id)
    if refund.return_request:
        return redirect('admin_return_detail', request_number=refund.return_request.request_number)
    
    # Fallback if no return request is attached (unlikely in our flow but just in case)
    messages.error(request, "This refund has no linked return request. Review not possible.")
    return redirect('admin_refunds')

@urbn_admin_required
def admin_analytics(request):
    import datetime
    from django.utils import timezone
    
    range_filter = request.GET.get('range', '30days')
    now = timezone.now()
    
    if range_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_filter == '7days':
        start_date = now - datetime.timedelta(days=7)
    elif range_filter == 'thismonth':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_filter == 'thisyear':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else: # 30days
        start_date = now - datetime.timedelta(days=30)
        
    orders_in_range = Order.objects.filter(created_at__gte=start_date)
    
    total_orders = orders_in_range.count()
    revenue_agg = orders_in_range.filter(payment_status='PAID').aggregate(Sum('total_amount'))
    total_revenue = revenue_agg['total_amount__sum'] or 0
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    total_products = Product.objects.count()
    settings = StoreSettings.load()
    # Find low stock by querying variants where stock - reserved_stock <= low_stock_threshold
    from django.db.models import F
    low_stock_products = ProductVariant.objects.filter(stock__lte=F('reserved_stock') + settings.low_stock_threshold).count()
    
    pending_orders = orders_in_range.filter(order_status='PLACED').count()
    return_requests = ReturnRequest.objects.filter(created_at__gte=start_date).count()
    refund_requests = Refund.objects.filter(created_at__gte=start_date).count()
    
    # We will pass empty chart data for now, or just the basic counts if we don't have time series ready.
    # To keep it lightweight and server-side, we'll just pass the counts to render simple charts.
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'pending_orders': pending_orders,
        'return_requests': return_requests,
        'refund_requests': refund_requests,
        'range_filter': range_filter,
    }
    return render(request, 'admin_dashboard/analytics.html', context)

@urbn_admin_required
def admin_settings(request):
    settings_obj = StoreSettings.load()
    if request.method == 'POST':
        try:
            settings_obj.store_name = request.POST.get('store_name', settings_obj.store_name)
            settings_obj.store_email = request.POST.get('store_email', settings_obj.store_email)
            settings_obj.low_stock_threshold = int(request.POST.get('low_stock_threshold', settings_obj.low_stock_threshold))
            settings_obj.return_window_days = int(request.POST.get('return_window_days', settings_obj.return_window_days))
            settings_obj.shipping_charge = request.POST.get('shipping_charge', settings_obj.shipping_charge)
            settings_obj.store_currency = request.POST.get('store_currency', settings_obj.store_currency)
            settings_obj.order_prefix = request.POST.get('order_prefix', settings_obj.order_prefix)
            settings_obj.save()
            messages.success(request, "Settings updated successfully.")
        except Exception as e:
            messages.error(request, f"Unable to save settings: {str(e)}")
        return redirect('admin_settings')
        
    import os
    razorpay_status = 'CONNECTED' if os.environ.get('RAZORPAY_KEY_SECRET') else 'NOT CONFIGURED'
    
    context = {
        'settings': settings_obj,
        'razorpay_status': razorpay_status
    }
    return render(request, 'admin_dashboard/settings.html', context)
