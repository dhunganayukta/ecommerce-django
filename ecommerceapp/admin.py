from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Contact, Product, Order, OrderUpdate
import json


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "date", "message_preview")
    search_fields = ("name", "email", "message")
    list_filter = ("date",)
    readonly_fields = ("date",)
    date_hierarchy = "date"
    list_per_page = 25

    def message_preview(self, obj):
        """Show first 50 characters of message"""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = "Message Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "is_new", "image_preview", "created_at")
    search_fields = ("name", "category", "description")
    list_filter = ("category", "is_new", "created_at")
    list_editable = ("price", "is_new", "rating")
    readonly_fields = ("created_at", "image_preview")
    date_hierarchy = "created_at"
    list_per_page = 20
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "category", "price", "rating")
        }),
        ("Product Details", {
            "fields": ("size", "description", "is_new")
        }),
        ("Media", {
            "fields": ("image", "image_preview")
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        })
    )

    def image_preview(self, obj):
        """Display small image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image Preview"

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related()


class OrderUpdateInline(admin.TabularInline):
    model = OrderUpdate
    extra = 0
    readonly_fields = ("timestamp",)
    fields = ("update_desc", "timestamp")
    ordering = ("-timestamp",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_id", 
        "customer_info", 
        "total_amount", 
        "status_colored", 
        "total_items", 
        "order_date"
    )
    # FIXED: Removed old name/email fields from search
    search_fields = ("id", "user__username", "user__email", "user__first_name", "user__last_name", "phone")
    list_filter = ("status", "order_date", "user__is_staff")
    inlines = [OrderUpdateInline]
    readonly_fields = ("id", "order_date", "updated_at", "items_display", "user_link", "customer_name", "customer_email")
    list_per_page = 25
    date_hierarchy = "order_date"
    
    # FIXED: Updated fieldsets to use new structure
    fieldsets = (
        ("Order Information", {
            "fields": ("id", "user_link", "status", "order_date", "updated_at")
        }),
        ("Customer Details", {
            "fields": ("customer_name", "customer_email", "phone")
        }),
        ("Shipping Address", {
            "fields": ("address1", "address2", "city", "state", "zip_code")
        }),
        ("Order Details", {
            "fields": ("amount", "items_display"),
        }),
    )

    def customer_info(self, obj):
        """Display customer name and email using new properties"""
        return format_html(
            "<strong>{}</strong><br/><small>{}</small>",
            obj.customer_name,
            obj.customer_email
        )
    customer_info.short_description = "Customer"

    def total_amount(self, obj):
        """Display formatted amount"""
        return f"Rs. {obj.amount:,.2f}"
    total_amount.short_description = "Amount"
    total_amount.admin_order_field = "amount"

    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'PENDING': '#ffc107',      # Warning yellow
            'PAID': '#28a745',         # Success green
            'FAILED': '#dc3545',       # Danger red
            'PROCESSING': '#17a2b8',   # Info blue
            'SHIPPED': '#6f42c1',      # Purple
            'DELIVERED': '#20c997',    # Teal
            'CANCELLED': '#6c757d',    # Gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Status"
    status_colored.admin_order_field = "status"

    def total_items(self, obj):
        """Display total number of items"""
        return obj.get_total_items()
    total_items.short_description = "Items"

    def items_display(self, obj):
        """Display formatted items in admin detail view"""
        try:
            items = json.loads(obj.items_json)
            html = "<table style='width: 100%; border-collapse: collapse;'>"
            html += "<tr style='background: #f8f9fa;'><th>Product</th><th>Size</th><th>Qty</th><th>Price</th></tr>"
            
            for item in items:
                try:
                    product = Product.objects.get(id=item.get('id'))
                    quantity = int(item.get('quantity', 1))
                    size = item.get('size', 'N/A')
                    subtotal = product.price * quantity
                    
                    html += f"""
                    <tr>
                        <td style='padding: 5px; border: 1px solid #ddd;'>{product.name}</td>
                        <td style='padding: 5px; border: 1px solid #ddd;'>{size}</td>
                        <td style='padding: 5px; border: 1px solid #ddd;'>{quantity}</td>
                        <td style='padding: 5px; border: 1px solid #ddd;'>Rs. {subtotal}</td>
                    </tr>
                    """
                except Product.DoesNotExist:
                    html += f"<tr><td colspan='4' style='padding: 5px; color: red;'>Product ID {item.get('id')} not found</td></tr>"
            
            html += "</table>"
            return mark_safe(html)
            
        except (json.JSONDecodeError, TypeError):
            return "Invalid items data"
    items_display.short_description = "Order Items"

    def user_link(self, obj):
        """Create link to user admin page"""
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "No User"
    user_link.short_description = "User Account"

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('user')

    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped']

    def mark_as_paid(self, request, queryset):
        """Bulk action to mark orders as paid"""
        updated = queryset.update(status='PAID')
        
        # Add order updates for each order
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                update_desc=f"Status changed to PAID by admin ({request.user.username})"
            )
        
        self.message_user(request, f"{updated} order(s) marked as paid.")
    mark_as_paid.short_description = "Mark selected orders as paid"

    def mark_as_processing(self, request, queryset):
        """Bulk action to mark orders as processing"""
        updated = queryset.update(status='PROCESSING')
        
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                update_desc=f"Status changed to PROCESSING by admin ({request.user.username})"
            )
        
        self.message_user(request, f"{updated} order(s) marked as processing.")
    mark_as_processing.short_description = "Mark selected orders as processing"

    def mark_as_shipped(self, request, queryset):
        """Bulk action to mark orders as shipped"""
        updated = queryset.update(status='SHIPPED')
        
        for order in queryset:
            OrderUpdate.objects.create(
                order=order,
                update_desc=f"Status changed to SHIPPED by admin ({request.user.username})"
            )
        
        self.message_user(request, f"{updated} order(s) marked as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"


@admin.register(OrderUpdate)
class OrderUpdateAdmin(admin.ModelAdmin):
    list_display = ("order_link", "update_desc_short", "timestamp")
    search_fields = ("order__id", "update_desc")
    list_filter = ("timestamp",)
    readonly_fields = ("timestamp",)
    date_hierarchy = "timestamp"
    list_per_page = 30

    def order_link(self, obj):
        """Create link to order admin page"""
        url = reverse("admin:ecommerceapp_order_change", args=[obj.order.pk])
        return format_html('<a href="{}">{}</a>', url, obj.order.id)
    order_link.short_description = "Order"
    order_link.admin_order_field = "order__id"

    def update_desc_short(self, obj):
        """Show shortened update description"""
        return obj.update_desc[:80] + "..." if len(obj.update_desc) > 80 else obj.update_desc
    update_desc_short.short_description = "Update Description"

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('order', 'order__user')


# Customize admin site headers
admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Admin Portal"
admin.site.index_title = "Welcome to E-Commerce Administration"