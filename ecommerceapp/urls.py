from django.urls import path
from ecommerceapp import views

urlpatterns = [
    # ==========================================
    # MAIN PAGES
    # ==========================================
    path('', views.index, name="index"),
    path('contact/', views.contact, name="contact"),
    path('about/', views.about, name="about"),
    path('profile/', views.profile, name="profile"),
    path('team/', views.team, name="team"),
    path('blog/', views.blog, name="blog"),
    
    # ==========================================
    # PRODUCT MANAGEMENT
    # ==========================================
    path("add-product/", views.add_product, name="add_product"),
    
    # ==========================================
    # ORDER MANAGEMENT
    # ==========================================
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<str:order_id>/", views.order_detail, name="order_detail"),
    path("orders/<str:order_id>/delete/", views.delete_order, name="delete_order"),
    path("orders/<str:order_id>/cancel/", views.cancel_order, name="cancel_order_alt"),  # Alternative URL
    path('cancel-order/<str:order_id>/', views.cancel_order, name='cancel_order'),  # ADD THIS LINE
    
    # ==========================================
    # PAYMENT INTEGRATION - eSewa
    # ==========================================
    path("esewa/payment/", views.esewa_payment, name="esewa_payment"),
    path("esewa/success/", views.esewa_success, name="esewa_success"),
    path("esewa/failure/", views.esewa_failure, name="esewa_failure"),
    
    # ==========================================
    # PAYMENT INTEGRATION - Khalti
    # ==========================================
    path('khalti/payment/', views.khalti_payment, name='khalti_payment'),
    path('khalti/verify/', views.khalti_verify, name='khalti_verify'),  # Fixed - removed order_id parameter
    path('khalti/webhook/', views.khalti_webhook, name='khalti_webhook'),
    path('khalti/test/', views.khalti_test_payment, name='khalti_test'),
]