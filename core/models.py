from django.db import models
from django.contrib.auth.models import User

def default_security_notifications():
    return {
        'new_login': True,
        'password_changed': True,
        'email_changed': True,
        '2fa_changes': True,
        'suspicious_login': True
    }

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.address_line_1}"

class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    new_email = models.EmailField()
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"OTP for {self.user.username} to {self.new_email}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    preferred_language = models.CharField(max_length=50, blank=True, null=True, default='English')
    clothing_size = models.CharField(max_length=10, blank=True, null=True)
    preferred_fit = models.CharField(max_length=50, blank=True, null=True)
    preferred_categories = models.JSONField(blank=True, default=list)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    security_notifications = models.JSONField(default=default_security_notifications, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    totp_secret = models.CharField(max_length=255, blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    recovery_codes = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"2FA status for {self.user.username}: {'Enabled' if self.is_enabled else 'Disabled'}"

class LoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_sessions')
    session_key = models.CharField(max_length=255, unique=True)
    device = models.CharField(max_length=255, blank=True, null=True)
    browser = models.CharField(max_length=255, blank=True, null=True)
    os = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session for {self.user.username} on {self.device}"

class SecurityEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=100)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event_type} at {self.timestamp}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart {self.session_key}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    selected_color = models.CharField(max_length=100, blank=True, null=True)
    selected_size = models.CharField(max_length=50, blank=True, null=True)
    selected_fit = models.CharField(max_length=100, blank=True, null=True)
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    placement = models.CharField(max_length=100, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} in cart {self.cart.id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PLACED', 'Placed'),
        ('PAYMENT_CONFIRMED', 'Payment Confirmed'),
        ('CONFIRMED', 'Confirmed'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Snapshot of Shipping Information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    # Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='INR')

    # Status
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    tracking_number = models.CharField(max_length=255, blank=True, null=True)

    # Razorpay Integration
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Invoicing
    invoice_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=100)
    
    # Snapshots
    product_name_snapshot = models.CharField(max_length=255)
    product_image_snapshot = models.CharField(max_length=500, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Variants
    size = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Customization
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    placement = models.CharField(max_length=100, blank=True, null=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name_snapshot} (Order: {self.order.order_number})"

    def save(self, *args, **kwargs):
        # Ensure subtotal is calculated based on snapshot price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()} at {self.created_at}"

class ReturnRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('RETURN', 'Return'),
        ('EXCHANGE', 'Exchange'),
        ('REPLACEMENT', 'Replacement'),
    ]

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PICKUP_SCHEDULED', 'Pickup Scheduled'),
        ('PICKED_UP', 'Picked Up'),
        ('RECEIVED', 'Received'),
        ('INSPECTING', 'Inspecting'),
        ('EXCHANGE_PROCESSING', 'Exchange Processing'),
        ('REPLACEMENT_PROCESSING', 'Replacement Processing'),
        ('REFUND_PROCESSING', 'Refund Processing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    request_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    reason = models.CharField(max_length=100)
    description = models.TextField()
    requested_quantity = models.PositiveIntegerField(default=1)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REQUESTED')
    
    # For Exchange
    requested_exchange_size = models.CharField(max_length=50, blank=True, null=True)
    requested_exchange_color = models.CharField(max_length=100, blank=True, null=True)
    
    admin_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.request_number} - {self.get_request_type_display()}"


class ReturnRequestImage(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='returns/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.return_request.request_number}"


class ReturnRequestStatusHistory(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30, choices=ReturnRequest.STATUS_CHOICES)
    note = models.TextField(blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.return_request.request_number} - {self.get_status_display()} at {self.created_at}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Collection(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='collections/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='collections/banners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    primary_image_url = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"
        
    @property
    def available_stock(self):
        return self.stock - self.reserved_stock

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"

class Refund(models.Model):
    STATUS_CHOICES = [
        ('REFUND_REQUESTED', 'Refund Requested'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
        ('REJECTED', 'Rejected')
    ]
    
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='refunds')
    return_request = models.OneToOneField('ReturnRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='refund')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REFUND_REQUESTED')
    razorpay_refund_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Refund {self.id} for Order {self.order.order_number}"

class AdminAuditLog(models.Model):
    admin_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    object_repr = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin_user} - {self.action} on {self.object_repr}"

class StoreSettings(models.Model):
    store_name = models.CharField(max_length=255, default='URBN Clothing')
    store_email = models.EmailField(default='vp05112007@gmail.com')
    low_stock_threshold = models.PositiveIntegerField(default=5)
    return_window_days = models.PositiveIntegerField(default=7)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    store_currency = models.CharField(max_length=10, default='INR')
    order_prefix = models.CharField(max_length=10, default='URBN')

    def save(self, *args, **kwargs):
        self.pk = 1
        super(StoreSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Store Settings"
