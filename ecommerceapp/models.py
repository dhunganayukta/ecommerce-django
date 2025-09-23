from django.db import models

# Category choices (can be extended)
CATEGORY_CHOICES = [
    ('mens', 'Mens'),
    ('womens', 'Womens'),
    ('kids', 'Kids'),
    ('accessories', 'Accessories'),
    ('newarrivals', 'New Arrivals'),
]

SIZE_CHOICES = [
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('XXL', 'Double XL'),
]

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default='M')
    image = models.ImageField(upload_to='products/')
    is_new = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    rating = models.FloatField(default=0)  # average rating
    rating_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.name
class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    items_json = models.TextField()
    name = models.CharField(max_length=100)
    email = models.EmailField()
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='Pending')
    
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} by {self.name}"
    
class OrderUpdate(models.Model):
    update_id = models.AutoField(primary_key=True)
    order_id = models.IntegerField(default="")
    update_desc = models.CharField(max_length=5000)
    delivered = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update {self.update_id} for Order {self.order_id}"