from django.urls import path
from ecommerceapp import views

urlpatterns = [
    path('', views.index, name="index"),
    path('contact/', views.contact, name="contact"),
    path('about/', views.about, name="about"),
    path('team/', views.team, name="team"),
    path('blog/', views.blog, name="blog"),
    path("add-product/", views.add_product, name="add_product"),
    path("checkout/", views.checkout, name="checkout"),
    

   path("esewa/payment/", views.esewa_payment, name="esewa_payment"),
    path("esewa/success/", views.esewa_success, name="esewa_success"),
    path("esewa/failure/", views.esewa_failure, name="esewa_failure"),
    path("khalti/verify/", views.khalti_verify, name="khalti_verify"),
]
