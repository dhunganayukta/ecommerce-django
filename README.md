
# 🛍️ Online Apparel Store

A modern, responsive e-commerce web application built with Django and Bootstrap for seamless online shopping experience.

## ✨ Features

- **Dynamic Product Catalog** - Browse products across multiple categories (Mens, Womens, Kids Wear, Accessories)
- **Real-time Filtering** - Isotope-powered filtering system for instant product discovery
- **Interactive Product Modals** - Detailed product views with image zoom, size selection, and quantity controls
- **Smart Shopping Cart** - Persistent cart using localStorage with real-time updates
- **Rating System** - Interactive star rating for products
- **Responsive Design** - Mobile-first approach ensuring great UX across all devices
- **New Arrivals Badge** - Highlight latest products in the catalog
- **Quick Checkout** - Streamlined "Buy Now" functionality





## 🛠️ Tech Stack

**Backend:**
- Django (Python web framework)
- Django Template Engine

**Frontend:**
- HTML5 & CSS3
- Bootstrap 5.3.3
- JavaScript (ES6+)

**Libraries & Plugins:**
- Isotope Layout - Product filtering and sorting
- GLightbox - Image lightbox functionality
- Bootstrap Icons - UI icons

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## ⚙️ Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/dhunganayukta/ecommerce-django.git
cd Project

Create virtual environment

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt

Run migrations

bashpython manage.py makemigrations
python manage.py migrate

Create superuser (admin)

bashpython manage.py createsuperuser

Collect static files

bashpython manage.py collectstatic

Run development server

bashpython manage.py runserver

Access the application


Frontend: http://127.0.0.1:8000/

Admin Panel: http://127.0.0.1:8000/admin/


🎯 Key Functionalities
Product Filtering
Products can be filtered by:

New Arrivals
Mens Collection
Womens Collection
Kids Wear
Accessories

Shopping Cart

Add/remove items
Update quantities
Persistent storage across sessions
Cart count indicator
Quick checkout access

Product Details Modal

High-quality product images with zoom
Size selection (S, M, L, XL, XXL)
Quantity selector
Star rating system
Add to Cart & Buy Now options