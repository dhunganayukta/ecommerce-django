# views.py
import uuid, os, requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils.text import slugify

from .models import Contact, Product, Orders, OrderUpdate

# ---------- Existing Views ----------

def index(request):
    categories = {
        'newarrivals': 'New Arrivals',
        'mens': 'Mens',
        'womens': 'Womens',
        'kids-wear': 'Kids',
        'accessories': 'Accessories',
    }
    products_by_category = {}
    for slug, name in categories.items():
        products = Product.objects.filter(category__iexact=name)
        for p in products:
            p.size_list = [s.strip() for s in p.size.split(',')] if p.size else ['S', 'M', 'L', 'XL', 'XXL']
        products_by_category[slug] = products

    return render(request, 'index.html', {'products_by_category': products_by_category})


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and message:
            Contact.objects.create(name=name, email=email, message=message)
            messages.success(request, "Your message has been sent.")
        else:
            messages.error(request, "All fields are required.")
    return render(request, "contact.html")


def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip()
        price = request.POST.get("price", "").strip()
        size = request.POST.get("size", "").strip()
        description = request.POST.get("description", "").strip()
        is_new = bool(request.POST.get("is_new", False))
        uploaded_file = request.FILES.get('image')

        if not all([name, category, price, size]):
            messages.error(request, "All product fields are required.")
            return redirect("add_product")
        if not uploaded_file:
            messages.error(request, "Please upload a product image.")
            return redirect("add_product")

        filename = f"{uuid.uuid4().hex}_{uploaded_file.name}"
        file_path = f"products/{filename}"
        save_path = os.path.join(settings.MEDIA_ROOT, file_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        Product.objects.create(
            name=name,
            category=category,
            price=price,
            size=size,
            image=file_path,
            is_new=is_new,
            description=description
        )
        messages.success(request, "Product added successfully.")
        return redirect("index")

    categories = ['Mens', 'Womens', 'Kids', 'Accessories', 'New Arrivals']
    sizes = ['S', 'M', 'L', 'XL', 'XXL']
    return render(request, "add_product.html", {"categories": categories, "sizes": sizes})


def about(request):
    return render(request, "about.html")


# ---------- Checkout & eSewa ----------

def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get("itemsJson", "").strip()
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        address1 = request.POST.get("address1", "").strip()
        address2 = request.POST.get("address2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        zip_code = request.POST.get("zip_code", "").strip()
        phone = request.POST.get("phone", "").strip()
        amount = request.POST.get("amount", "").strip()

        if not all([items_json, name, email, address1, city, state, zip_code, phone, amount]):
            messages.error(request, "All fields are required.")
            return redirect("checkout")

        order = Orders.objects.create(
            items_json=items_json,
            name=name,
            email=email,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            amount=amount,
            payment_status='Pending'
        )
        OrderUpdate.objects.create(order_id=order.order_id, update_desc="Order Placed")

        # Redirect to Khalti payment page
        khalti_data = {
            "public_key": "test_public_key_1234567890abcdef",
            "product_identity": str(order.order_id),
            "product_name": "Order {}".format(order.order_id),
            "amount": int(float(amount) * 100),  # Amount in paisa
            "product_url": request.build_absolute_uri('/'),
            "return_url": request.build_absolute_uri('/khalti-success/'),
            "cancel_url": request.build_absolute_uri('/khalti-failure/'),
        }
        return render(request, "khalti_payment.html", {"khalti_data": khalti_data})

    return render(request, "checkout.html")