from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import security_views
from . import cart_views
from . import checkout_views
from . import order_views
from . import order_views
from . import api_views
from . import admin_views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('clone/', views.clone, name='clone'),
    path('home.html', views.home, name='home'),
    path('categories.html', views.categories, name='categories'),
    path('trending.html', views.trending, name='trending'),
    path('collections.html', views.collections, name='collections'),
    path('customize.html', views.customize, name='customize'),
    path('cart.html', views.cart, name='cart'),
    
    # Cart API
    path('api/cart/', cart_views.get_cart, name='get_cart'),
    path('api/cart/add/', cart_views.add_to_cart, name='add_to_cart'),
    path('api/cart/update/<int:item_id>/', cart_views.update_cart_item, name='update_cart_item'),
    path('api/cart/remove/<int:item_id>/', cart_views.remove_cart_item, name='remove_cart_item'),
    
    # Storefront APIs
    path('api/products/', api_views.get_products, name='get_products'),
    path('api/collections/', api_views.get_collections, name='get_collections'),
    
    # Profile & Account Management
    path('profile/', views.profile, name='profile'),
    path('api/profile/update/', views.update_profile, name='update_profile'),
    path('api/profile/password/change/', views.change_password, name='change_password'),
    
    # Address CRUD
    path('api/profile/address/add/', views.add_address, name='add_address'),
    path('api/profile/address/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('api/profile/address/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('api/profile/address/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    
    # Email Change OTP Flow
    path('api/profile/email/request-change/', views.request_email_change, name='request_email_change'),
    path('api/profile/email/verify/', views.verify_email_change, name='verify_email_change'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='password_reset_complete'),
    
    # Security Features
    path('api/profile/photo/upload/', security_views.upload_profile_photo, name='upload_profile_photo'),
    path('api/profile/photo/remove/', security_views.remove_profile_photo, name='remove_profile_photo'),
    path('api/security/2fa/request/', security_views.enable_2fa_request, name='enable_2fa_request'),
    path('api/security/2fa/verify/', security_views.verify_enable_2fa, name='verify_enable_2fa'),
    path('api/security/2fa/disable/', security_views.disable_2fa, name='disable_2fa'),
    path('api/security/session/logout/', security_views.logout_session, name='logout_session'),
    path('api/security/session/logout-all/', security_views.logout_all_other_sessions, name='logout_all_other_sessions'),
    path('api/security/notifications/update/', security_views.update_security_notifications, name='update_security_notifications'),
    # Checkout & Payments
    path('checkout/', checkout_views.checkout_page, name='checkout'),
    path('checkout/create-payment/', checkout_views.create_razorpay_order, name='create_razorpay_order'),
    path('checkout/payment-success/', checkout_views.payment_success, name='payment_success'),
    path('payments/razorpay/webhook/', checkout_views.razorpay_webhook, name='razorpay_webhook'),

    # Orders
    path('orders/', order_views.my_orders, name='my_orders'),
    path('orders/<str:order_number>/', order_views.order_details, name='order_details'),
    path('orders/<str:order_number>/tracking/', order_views.order_tracking, name='order_tracking'),
    path('orders/<str:order_number>/confirmed/', order_views.order_confirmation, name='order_confirmation'),
    path('orders/<str:order_number>/invoice/download/', order_views.download_invoice, name='download_invoice'),
    path('orders/<str:order_number>/invoice/resend/', order_views.resend_invoice, name='resend_invoice'),
    
    # Returns
    path('orders/<str:order_number>/<int:item_id>/return/', order_views.create_return_request, name='create_return_request'),
    path('returns/', order_views.return_requests_list, name='return_requests_list'),
    path('returns/<str:request_number>/', order_views.return_request_detail, name='return_request_detail'),

    # Admin Dashboard
    path('admin-dashboard/', admin_views.dashboard_home, name='admin_dashboard'),
    path('admin-dashboard/orders/', admin_views.admin_orders, name='admin_orders'),
    path('admin-dashboard/orders/<str:order_number>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('admin-dashboard/products/', admin_views.admin_products, name='admin_products'),
    path('admin-dashboard/products/<str:sku>/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('admin-dashboard/categories/', admin_views.admin_categories, name='admin_categories'),
    path('admin-dashboard/collections/', admin_views.admin_collections, name='admin_collections'),
    path('admin-dashboard/returns/', admin_views.admin_returns, name='admin_returns'),
    path('admin-dashboard/returns/<str:request_number>/', admin_views.admin_return_detail, name='admin_return_detail'),
    path('admin-dashboard/returns/<str:request_number>/refund/', admin_views.admin_process_refund, name='admin_process_refund'),
    path('admin-dashboard/users/', admin_views.admin_users, name='admin_users'),
    path('admin-dashboard/inventory/', admin_views.admin_inventory, name='admin_inventory'),
    path('admin-dashboard/refunds/', admin_views.admin_refunds, name='admin_refunds'),
    path('admin-dashboard/refunds/<int:refund_id>/', admin_views.admin_refund_detail, name='admin_refund_detail'),
    path('admin-dashboard/analytics/', admin_views.admin_analytics, name='admin_analytics'),
    path('admin-dashboard/settings/', admin_views.admin_settings, name='admin_settings'),
]
