from django.shortcuts import render, redirect
from django.contrib import messages
from ecommerceapp.models import Contact, Product, Category
import os
from django.conf import settings

def index(request):
    # categories and their slugs
    categories = {
        'newarrivals': 'New Arrivals',
        'mens': "Mens",
        'womens': "Womens",
        'kids-wear': 'Kids Wear',
        'accessories': 'Accessories'
    }

    products_by_category = {}
    for slug, cat_name in categories.items():
        cat = Category.objects.filter(name=cat_name).first()          # ✅ filter, not objects()
        if cat:
            products_by_category[slug] = Product.objects.filter(category=cat)  # ✅ filter
        else:
            products_by_category[slug] = []  # empty list if category not found

    return render(request, "index.html", {'products_by_category': products_by_category})


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        description = request.POST.get("description", "")
        phonenumber = request.POST.get("phonenumber", "")

        Contact.objects.create(                     # ✅ use create() for clarity
            name=name,
            email=email,
            description=description,
            phonenumber=phonenumber
        )
        messages.success(request, "Your message has been sent.")

    return render(request, "contact.html")


def about(request):
    return render(request, "about.html")


def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category_name = request.POST.get("category")
        uploaded_file = request.FILES['image']

        # Save image into MEDIA_ROOT/products/
        file_path = f"products/{uploaded_file.name}"
        save_path = os.path.join(settings.MEDIA_ROOT, file_path)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        # Get Category object
        cat = Category.objects.filter(name=category_name).first()      # ✅ filter
        if not cat:
            messages.error(request, "Category not found!")
            return redirect("add_product")

        # Save product
        Product.objects.create(                                        # ✅ create
            name=name,
            category=cat,
            image=file_path
        )

        messages.success(request, "Product added successfully.")
        return redirect("index")

    # Pass categories to template for select dropdown
    categories = Category.objects.all()
    return render(request, "add_product.html", {"categories": categories})
