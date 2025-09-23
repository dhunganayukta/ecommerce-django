from django.contrib import admin
from .models import Product, Contact, Order, OrderUpdate

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'size', 'is_new')
    list_filter = ('category', 'size', 'is_new')
    search_fields = ('name', 'category')
    ordering = ('category', 'name')
    list_editable = ('price', 'size', 'is_new')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message')
    search_fields = ('name', 'email')
    ordering = ('name',)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'name', 'email', 'amount', 'payment_status', 'order_date')
    search_fields = ('order_id', 'name', 'email')
    list_filter = ('payment_status', 'order_date')
    ordering = ('-order_date',) # Newest orders first
    readonly_fields = ('order_date',)  # Prevent editing order date

@admin.register(OrderUpdate)
class OrderUpdateAdmin(admin.ModelAdmin):
    list_display = ('update_id', 'order_id', 'delivered', 'timestamp')
    search_fields = ('order_id',)
    list_filter = ('delivered', 'timestamp')
    ordering = ('-timestamp',) # Newest updates first   
    readonly_fields = ('timestamp',)  # Prevent editing timestamp