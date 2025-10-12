from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)  # Add this
    subject = models.CharField(max_length=200, default='General Inquiry') 
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Mens", "Mens"),
        ("Womens", "Womens"),
        ("Kids", "Kids"),
        ("Accessories", "Accessories"),
        ("New Arrivals", "New Arrivals"),
    ]

    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double XL'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=100, help_text="Comma-separated sizes e.g. S,M,L,XL")
    image = models.ImageField(upload_to="products/")
    is_new = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=0.0
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("PROCESSING", "Processing"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    # Custom ID as primary key
    id = models.CharField(
        max_length=50, 
        primary_key=True,
        editable=False
    )

    # Connect order to Django's default User - MAIN RELATIONSHIP
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Cart / items
    items_json = models.TextField()  # stores cart in JSON

    # REMOVED: name and email (now accessed via user.get_full_name() and user.email)

    # Shipping details
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)

    # Payment
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    # Metadata
    order_date = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate custom id only if it's not set
        if not self.id:
            self.id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            # Ensure uniqueness (very unlikely to collide, but just in case)
            while Order.objects.filter(id=self.id).exists():
                self.id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username if self.user else 'Unknown'} - Rs. {self.amount}"

    class Meta:
        ordering = ['-order_date']

    # CONVENIENCE PROPERTIES to access user data easily
    @property
    def customer_name(self):
        """Get customer name from User model"""
        if not self.user:
            return "Guest Customer"
        return self.user.get_full_name() or self.user.username
    
    @property 
    def customer_email(self):
        """Get customer email from User model"""
        if not self.user:
            return "No email"
        return self.user.email

    def get_total_items(self):
        """Get total number of items in the order"""
        try:
            import json
            items = json.loads(self.items_json)
            return sum(int(item.get('quantity', 1)) for item in items)
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0

    def get_status_display_class(self):
        """Get CSS class for status display"""
        status_classes = {
            'PENDING': 'text-warning',
            'PAID': 'text-success',
            'FAILED': 'text-danger',
            'PROCESSING': 'text-info',
            'SHIPPED': 'text-primary',
            'DELIVERED': 'text-success',
            'CANCELLED': 'text-danger',
        }
        return status_classes.get(self.status, 'text-secondary')

    @property
    def order_id(self):
        """Backward compatibility property for templates that might use order_id"""
        return self.id


class OrderUpdate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="updates", null=True, blank=True)
    update_desc = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.order:
            return f"Update for Order {self.order.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        return f"Orphaned update at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp']



class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    khalti_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.payment_status}"
    
    class Meta:
        ordering = ['-created_at']