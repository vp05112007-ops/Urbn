import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "urbn_project.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Product, Category, Cart, CartItem, Order, OrderItem, OrderStatusHistory,
    ReturnRequest, ReturnRequestImage, ReturnRequestStatusHistory, Profile, Address
)

def print_counts():
    counts = {
        "User": User.objects.count(),
        "Profile": Profile.objects.count(),
        "Address": Address.objects.count(),
        "Category": Category.objects.count(),
        "Product": Product.objects.count(),
        "Cart": Cart.objects.count(),
        "CartItem": CartItem.objects.count(),
        "Order": Order.objects.count(),
        "OrderItem": OrderItem.objects.count(),
        "OrderStatusHistory": OrderStatusHistory.objects.count(),
        "ReturnRequest": ReturnRequest.objects.count(),
        "ReturnRequestImage": ReturnRequestImage.objects.count(),
        "ReturnRequestStatusHistory": ReturnRequestStatusHistory.objects.count(),
    }
    for k, v in counts.items():
        print(f"{k}: {v}")

if __name__ == '__main__':
    print_counts()
