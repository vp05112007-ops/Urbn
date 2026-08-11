from django.contrib import admin
from .models import (
    Address, EmailVerificationOTP, UserProfile, TwoFactorAuth,
    LoginSession, SecurityEvent, Cart, CartItem,
    Order, OrderItem, OrderStatusHistory
)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'is_default')
    search_fields = ('user__username', 'full_name', 'city')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'phone')
    search_fields = ('user__username', 'user__email')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name_snapshot', 'product_id', 'unit_price', 'size', 'color', 'quantity', 'custom_text', 'placement', 'subtotal')
    can_delete = False

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'message', 'created_at')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'payment_status', 'order_status', 'invoice_sent', 'created_at')
    list_filter = ('payment_status', 'order_status', 'invoice_sent', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('order_number', 'subtotal', 'shipping_charge', 'discount', 'total_amount', 'currency', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'invoice_sent')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    actions = ['resend_invoice_action']

    @admin.action(description='Resend Invoice Email to Selected Orders')
    def resend_invoice_action(self, request, queryset):
        from core.invoice import send_invoice_email
        success_count = 0
        error_count = 0
        for order in queryset:
            # Bypass the idempotent check to force resend
            order.invoice_sent = False 
            success, msg = send_invoice_email(order, request=request)
            if success:
                success_count += 1
            else:
                error_count += 1
        
        if success_count:
            self.message_user(request, f"Successfully resent invoices for {success_count} order(s).")
        if error_count:
            self.message_user(request, f"Failed to send invoices for {error_count} order(s).", level='ERROR')

    def save_model(self, request, obj, form, change):
        if change:
            orig_obj = Order.objects.get(pk=obj.pk)
            if orig_obj.order_status != obj.order_status:
                OrderStatusHistory.objects.create(
                    order=obj,
                    status=obj.order_status,
                    message=f"Status manually updated by admin {request.user.username}"
                )
        super().save_model(request, obj, form, change)

admin.site.register(EmailVerificationOTP)
admin.site.register(TwoFactorAuth)
admin.site.register(LoginSession)
admin.site.register(SecurityEvent)
admin.site.register(Cart)
admin.site.register(CartItem)

from .models import ReturnRequest, ReturnRequestImage, ReturnRequestStatusHistory
from django.utils.html import format_html

class ReturnRequestImageInline(admin.TabularInline):
    model = ReturnRequestImage
    extra = 0
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px;" /></a>', obj.image.url)
        return ""
    image_preview.short_description = "Image Preview"

class ReturnRequestStatusHistoryInline(admin.TabularInline):
    model = ReturnRequestStatusHistory
    extra = 0
    readonly_fields = ['status', 'note', 'changed_by', 'created_at']
    can_delete = False

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'order', 'user', 'get_product_name', 'request_type', 'reason', 'status', 'created_at']
    list_filter = ['request_type', 'status', 'reason', 'created_at']
    search_fields = ['request_number', 'order__order_number', 'user__email', 'user__username']
    readonly_fields = ['request_number', 'order', 'order_item', 'user', 'request_type', 'reason', 'description', 'requested_quantity', 'requested_exchange_size', 'requested_exchange_color', 'created_at', 'updated_at', 'approved_at', 'completed_at']
    inlines = [ReturnRequestImageInline, ReturnRequestStatusHistoryInline]
    actions = ['mark_approved', 'mark_pickup_scheduled', 'mark_received', 'mark_inspecting', 'mark_completed']
    
    def get_product_name(self, obj):
        return obj.order_item.product_name_snapshot
    get_product_name.short_description = 'Product'

    def save_model(self, request, obj, form, change):
        if change:
            orig_obj = ReturnRequest.objects.get(pk=obj.pk)
            if orig_obj.status != obj.status:
                ReturnRequestStatusHistory.objects.create(
                    return_request=obj,
                    status=obj.status,
                    note=f"Status changed to {obj.get_status_display()} by {request.user.username}",
                    changed_by=request.user
                )
                
                from .returns import send_return_status_email
                send_return_status_email(obj, request=request)
                
                from django.utils import timezone
                if obj.status == 'APPROVED' and not obj.approved_at:
                    obj.approved_at = timezone.now()
                if obj.status == 'COMPLETED' and not obj.completed_at:
                    obj.completed_at = timezone.now()
                    
        super().save_model(request, obj, form, change)
        
    @admin.action(description="Approve Selected Requests")
    def mark_approved(self, request, queryset):
        for obj in queryset:
            if obj.status in ['REQUESTED', 'UNDER_REVIEW']:
                obj.status = 'APPROVED'
                obj.save()
                self.save_model(request, obj, None, True)
        self.message_user(request, "Selected requests have been approved.")

    @admin.action(description="Schedule Pickup for Selected")
    def mark_pickup_scheduled(self, request, queryset):
        for obj in queryset:
            obj.status = 'PICKUP_SCHEDULED'
            obj.save()
            self.save_model(request, obj, None, True)
            
    @admin.action(description="Mark Received")
    def mark_received(self, request, queryset):
        for obj in queryset:
            obj.status = 'RECEIVED'
            obj.save()
            self.save_model(request, obj, None, True)
            
    @admin.action(description="Start Inspection")
    def mark_inspecting(self, request, queryset):
        for obj in queryset:
            obj.status = 'INSPECTING'
            obj.save()
            self.save_model(request, obj, None, True)
            
    @admin.action(description="Complete Selected Requests")
    def mark_completed(self, request, queryset):
        for obj in queryset:
            obj.status = 'COMPLETED'
            obj.save()
            self.save_model(request, obj, None, True)
