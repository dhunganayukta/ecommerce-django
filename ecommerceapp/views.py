# views.py
import uuid, os, requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils.text import slugify
from .models import Contact, Product, Order, OrderUpdate
from decimal import Decimal, InvalidOperation
import json


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
        items_json = request.POST.get("itemsJson")
        amt_str = request.POST.get("amt", "").strip()

        from decimal import Decimal, InvalidOperation
        try:
            amount = Decimal(amt_str)
        except (InvalidOperation, TypeError):
            messages.error(request, "Invalid amount. Please try again.")
            return redirect("checkout")

        order = Order.objects.create(
            items_json=items_json,
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            address1=request.POST.get("address1"),
            address2=request.POST.get("address2"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            zip_code=request.POST.get("zip_code"),
            phone=request.POST.get("phone"),
            amount=amount,
        )

        # Clear the cart/session after order is saved
        if "cart" in request.session:
            del request.session["cart"]

        context = {
            "thank": True,
            "id": order.order_id
        }
        return render(request, "checkout.html", context)

    return render(request, "checkout.html")




# -------------------------------
# eSewa Integration
# -------------------------------
def esewa_payment(request):
    """
    Redirects to eSewa Sandbox with required parameters.
    """
    order_id = request.GET.get("order_id", f"ORDER_{uuid.uuid4().hex[:6]}")
    amt = request.GET.get("amt", "1000")

    context = {
        "amt": amt,
        "pid": order_id,
        "scd": "EPAYTEST",  # eSewa sandbox merchant code
        "su": request.build_absolute_uri("/esewa/success/"),
        "fu": request.build_absolute_uri("/esewa/failure/"),
        "esewa_url": "https://uat.esewa.com.np/epay/main"  # sandbox base url
    }
    return render(request, "esewa_payment.html", context)


def esewa_success(request):
    """
    Handles eSewa success callback.
    eSewa returns: amt, oid (order id), refId (transaction id)
    """
    amt = request.GET.get("amt")
    oid = request.GET.get("oid")
    ref_id = request.GET.get("refId")

    context = {
        "amt": amt,
        "oid": oid,
        "ref_id": ref_id,
    }
    return render(request, "success.html", context)


def esewa_failure(request):

    return render(request, "failure.html")


# -------------------------------
# Khalti Integration (Sandbox)
# -------------------------------
def khalti_verify(request):
    """
    Verifies Khalti payment token with Sandbox API.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")
        amount = data.get("amount")

        url = "https://khalti.com/api/v2/payment/verify/"
        payload = {"token": token, "amount": amount}
        headers = {"Authorization": "Key test_secret_key_6f30ecb6c8c94db1a6c3b02da6b6f0ef"}

        response = requests.post(url, data=payload, headers=headers)
        resp_json = response.json()

        if response.status_code == 200:
            return JsonResponse({"success": True, "message": "Khalti payment verified!", "details": resp_json})
        else:
            return JsonResponse({"success": False, "message": "Payment verification failed!", "details": resp_json})

    return JsonResponse({"success": False, "message": "Invalid request"})
def team(request):
    return render(request, "team.html") 

def blog(request):
    return render(request, "blog.html")
