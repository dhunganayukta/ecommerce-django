from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Product, Order, OrderUpdate, Contact, Payment
import json
import requests
import uuid
from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


# ==========================================
# KHALTI CONFIGURATION - CORRECTED
# ==========================================
KHALTI_PUBLIC_KEY = "1cb68e2d20934fb6811c17e2b2f00601"
KHALTI_SECRET_KEY = "Key 1dc34425927c457f9bbeb360a5d3a620"  # Added "Key " prefix
KHALTI_VERIFY_URL = "https://test-admin.khalti.com/api/v2/payment/verify/"
KHALTI_MODE = 'test'



# ==========================================
# MAIN PAGES
# ==========================================
def index(request):
    """Home page with featured products - All categories separate, New Arrivals shows 8 newest"""
    # Get all products
    all_products = Product.objects.all()
    
    # Get ONLY 8 new arrivals (limited, these will ONLY appear in new arrivals filter)
    new_arrivals = Product.objects.filter(is_new=True).order_by('-id')[:8]
    
    # Group products by their actual category
    products_by_category = {}
    
    # Add new arrivals as a separate filter category (only these 8 products)
    products_by_category['new-arrival'] = list(new_arrivals)
    
    # Add ALL products to their respective category filters (including new arrivals)
    for product in all_products:
        # Use the exact category from database
        # Convert to lowercase and replace spaces with hyphens for CSS class
        category_key = product.category.lower().replace(' ', '-')
        
        # Normalize category names to match filter buttons
        if category_key in ['kids', 'kids wear', 'kids_wear', 'kidswear', 'kids-wear']:
            category_key = 'kids-wear'
        elif category_key in ['new-arrivals', 'new arrival', 'new_arrivals']:
            # Skip products with "New Arrivals" as their actual category
            # (they should be categorized as Mens/Womens/Kids/Accessories instead)
            continue
        
        if category_key not in products_by_category:
            products_by_category[category_key] = []
        
        products_by_category[category_key].append(product)
    
    context = {
        'products': all_products[:8],
        'products_by_category': products_by_category,
        'new_arrivals': new_arrivals,
        'khalti_public_key': KHALTI_PUBLIC_KEY,
    }
    
    # Debug: Print to console to verify
    print(f"Total products: {all_products.count()}")
    print(f"New arrivals (limited to 8): {len(new_arrivals)}")
    print(f"Categories found: {list(products_by_category.keys())}")
    for cat, prods in products_by_category.items():
        print(f"  {cat}: {len(prods)} products")
        if cat == 'kids-wear':
            print(f"    Kids products: {[p.name for p in prods]}")
    
    return render(request, 'index.html', context)


def contact(request):
    """Contact page - handle contact form submissions"""
    if request.method == "POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', 'General Inquiry')
        message = request.POST.get('message', '')
        
        # Save contact message
        contact_msg = Contact(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        contact_msg.save()
        
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
    
    return render(request, 'contact.html')


def about(request):
    """About page"""
    return render(request, 'about.html')


def team(request):
    """Team page"""
    return render(request, 'team.html')


def blog(request):
    """Blog page"""
    return render(request, 'blog.html')


@login_required
def profile(request):
    """User profile page"""
    user = request.user
    recent_orders = Order.objects.filter(user=user).order_by('-order_date')[:5]
    
    # Count orders by status
    pending_orders = Order.objects.filter(user=user, status='PENDING').count()
    processing_orders = Order.objects.filter(user=user, status__in=['PROCESSING', 'SHIPPED']).count()
    delivered_orders = Order.objects.filter(user=user, status='DELIVERED').count()
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'delivered_orders': delivered_orders,
        'total_orders': Order.objects.filter(user=user).count(),
    }
    return render(request, 'profile.html', context)


# ==========================================
# PRODUCT MANAGEMENT
# ==========================================
@login_required
def add_product(request):
    """Add new product - Admin only"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add products.')
        return redirect('index')
    
    if request.method == "POST":
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        size = request.POST.get('size')
        description = request.POST.get('description', '')
        is_new = request.POST.get('is_new') == 'on'
        image = request.FILES.get('image')
        
        product = Product(
            name=name,
            category=category,
            price=price,
            size=size,
            description=description,
            is_new=is_new,
            image=image
        )
        product.save()
        
        messages.success(request, 'Product added successfully!')
        return redirect('index')
    
    return render(request, 'add_product.html')


# ==========================================
# CHECKOUT & ORDER MANAGEMENT
# ==========================================
@login_required
def checkout(request):
    """Checkout page with payment options"""
    if request.method == "POST":
        # Get cart items from POST data
        items_json = request.POST.get('itemsJson', '[]')
        amt = request.POST.get('amt', '0')
        
        # Get shipping details
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        
        # Validate cart data
        try:
            items = json.loads(items_json)
            if not items or len(items) == 0:
                messages.error(request, 'Your cart is empty!')
                return redirect('checkout')
            
            # Calculate and validate amount
            calculated_amount = sum(
                float(item.get('price', 0)) * int(item.get('quantity', 1)) 
                for item in items
            )
            
            submitted_amount = float(amt)
            
            # Check if amounts match (allow small difference for rounding)
            if abs(calculated_amount - submitted_amount) > 0.01:
                messages.error(request, 'Cart total mismatch. Please refresh and try again.')
                return redirect('checkout')
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            messages.error(request, 'Invalid cart data. Please refresh and try again.')
            print(f"Cart validation error: {e}")
            return redirect('checkout')
        
        # Create order
        order = Order(
            user=request.user,
            items_json=items_json,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            amount=Decimal(str(calculated_amount)),
            status='PENDING'
        )
        order.save()
        
        # Create initial order update
        update = OrderUpdate(
            order=order,
            update_desc="Order has been placed"
        )
        update.save()
        
        # Store order_id in session for payment
        request.session['pending_order_id'] = order.id
        
        # Render thank you page with order details
        try:
            order_items = []
            for item in items:
                order_items.append({
                    'product': type('obj', (object,), {
                        'name': item.get('name', 'Unknown'),
                        'price': item.get('price', 0)
                    }),
                    'size': item.get('size', 'N/A'),
                    'quantity': item.get('quantity', 1),
                    'subtotal': float(item.get('price', 0)) * int(item.get('quantity', 1))
                })
        except Exception as e:
            print(f"Error parsing order items: {e}")
            order_items = []
        
        context = {
            'thank': True,
            'order': order,
            'order_date': order.order_date,
            'order_items': order_items,
            'total_amount': order.amount,
        }
        
        return render(request, 'checkout.html', context)
    
    # GET request - show checkout form
    context = {
        'khalti_public_key': KHALTI_PUBLIC_KEY,
    }
    return render(request, 'checkout.html', context)


@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    context = {
        'orders': orders,
    }
    return render(request, 'order_history.html', context)


@login_required
def order_detail(request, order_id):
    """Display detailed information about a specific order"""
    # Get order by id (which is the primary key CharField in your model)
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, f'Order not found: {order_id}')
        return redirect('order_history')
    
    # Parse items JSON
    try:
        items = json.loads(order.items_json)
    except json.JSONDecodeError:
        items = []
    
    # Transform items into order_items format expected by template
    order_items = []
    for item in items:
        try:
            # Create a mock product object for template compatibility
            order_items.append({
                'product': type('obj', (object,), {
                    'id': item.get('id', ''),
                    'name': item.get('name', 'Unknown Product'),
                    'price': float(item.get('price', 0)),
                    'category': item.get('category', 'General'),
                    'image': type('obj', (object,), {
                        'url': item.get('image', '')
                    })
                }),
                'size': item.get('size', 'N/A'),
                'quantity': int(item.get('quantity', 1)),
                'subtotal': float(item.get('price', 0)) * int(item.get('quantity', 1))
            })
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error parsing item: {e}")
            continue
    
    # Get order updates
    order_updates = OrderUpdate.objects.filter(order=order).order_by('-timestamp')
    
    context = {
        'order': order,
        'items': items,  # Raw items for any other use
        'order_items': order_items,  # Formatted items for template
        'order_updates': order_updates,
    }
    return render(request, 'order_details.html', context)


@login_required
def delete_order(request, order_id):
    """
    Delete a pending order (only if payment is not completed)
    """
    if request.method != 'POST':
        return redirect('order_history')
    
    # Get the order and ensure it belongs to the current user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow deletion of pending/unpaid orders
    if order.status not in ['Pending', 'pending', 'PENDING']:
        messages.error(request, 'Cannot delete an order that has been paid or is being processed.')
        return redirect('order_detail', order_id=order_id)
    
    # Store order details for the success message
    order_number = order.id
    
    # Delete the order (this will also delete related OrderItems if CASCADE is set)
    order.delete()
    
    messages.success(request, f'Order #{order_number} has been successfully cancelled.')
    return redirect('order_history')


@login_required
def cancel_order(request, order_id):
    """
    Cancel a pending order by updating its status instead of deleting
    """
    if request.method != 'POST':
        return redirect('order_history')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow cancellation of pending/unpaid orders
    if order.status not in ['Pending', 'pending', 'PENDING']:
        messages.error(request, 'Cannot cancel an order that has been paid or is being processed.')
        return redirect('order_detail', order_id=order_id)
    
    # Update status to cancelled
    order.status = 'CANCELLED'
    order.save()
    
    # Add order update
    update = OrderUpdate(
        order=order,
        update_desc="Order cancelled by customer"
    )
    update.save()
    
    messages.success(request, f'Order #{order.id} has been successfully cancelled.')
    return redirect('order_history')


# ==========================================
# KHALTI PAYMENT INTEGRATION - UPDATED
# ==========================================
@login_required
def khalti_payment(request):
    """Khalti payment initiation page"""
    # Get order_id from GET parameter or session
    order_id = request.GET.get('order_id') or request.session.get('pending_order_id')
    
    if not order_id:
        messages.error(request, 'No pending order found')
        return redirect('checkout')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Convert amount to paisa (Khalti uses paisa)
    amount_in_paisa = int(order.amount * 100)
    
    logger.info(f"Khalti payment initiated for order {order_id}, amount: Rs. {order.amount}")
    
    context = {
        'order': order,
        'amount_in_paisa': amount_in_paisa,
        'khalti_public_key': KHALTI_PUBLIC_KEY,
        'khalti_mode': KHALTI_MODE,
    }
    
    return render(request, 'khalti_payment.html', context)


@csrf_exempt
@login_required
def khalti_verify(request, order_id):
    """
    Verify Khalti payment after user completes payment
    This endpoint is called from the frontend after successful payment
    """
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            
            token = data.get('token')
            amount = data.get('amount')  # Amount in paisa
            
            logger.info(f"Khalti verification request - Order: {order_id}, Token: {token}, Amount: {amount}")
            
            if not token or not amount:
                logger.error("Missing token or amount in verification request")
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required parameters'
                }, status=400)
            
            # Get order and verify it belongs to the user
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Verify amount matches
            expected_amount = int(order.amount * 100)
            if int(amount) != expected_amount:
                logger.error(f"Amount mismatch: expected {expected_amount}, got {amount}")
                return JsonResponse({
                    'success': False,
                    'message': 'Amount mismatch'
                }, status=400)
            
            # Verify payment with Khalti using CORRECTED configuration
            headers = {
                'Authorization': KHALTI_SECRET_KEY,  # Already has "Key " prefix
                'Content-Type': 'application/json',
            }
            
            payload = {
                'token': token,
                'amount': amount
            }
            
            logger.info(f"Sending verification request to: {KHALTI_VERIFY_URL}")
            
            response = requests.post(
                KHALTI_VERIFY_URL,
                json=payload,  # Use json parameter instead of data
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Khalti response status: {response.status_code}")
            logger.info(f"Khalti response body: {response.text}")
            
            response_data = response.json()
            
            # Check if payment was successful
            if response.status_code == 200:
                # Update order status
                order.status = 'PAID'
                order.save()
                
                # Create payment record
                payment = Payment(
                    order=order,
                    payment_method='khalti',
                    amount=Decimal(str(amount)) / 100,  # Convert paisa to rupees
                    payment_status='completed',
                    transaction_id=response_data.get('idx'),
                    khalti_response=response_data
                )
                payment.save()
                
                # Create order update
                update = OrderUpdate(
                    order=order,
                    update_desc=f"Payment of Rs. {order.amount} completed via Khalti. Transaction ID: {response_data.get('idx')}"
                )
                update.save()
                
                # Clear session
                if 'pending_order_id' in request.session:
                    del request.session['pending_order_id']
                
                logger.info(f"Payment verified successfully for order {order.id}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Payment verified successfully',
                    'order_id': order.id,
                    'transaction_id': response_data.get('idx'),
                    'redirect_url': f'/orders/{order.id}/'
                })
            else:
                # Payment verification failed
                error_message = response_data.get('error_key', response_data.get('detail', 'Unknown error'))
                logger.error(f"Payment verification failed: {error_message}")
                
                return JsonResponse({
                    'success': False,
                    'message': f'Payment verification failed: {error_message}',
                    'error': response_data
                }, status=400)
                
        except Order.DoesNotExist:
            logger.error(f"Order not found during verification: {order_id}")
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)
            
        except requests.RequestException as e:
            logger.exception(f"Network error during Khalti verification: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Network error: {str(e)}'
            }, status=500)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
            
        except Exception as e:
            logger.exception(f"Unexpected error during verification: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Server error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


@csrf_exempt
def khalti_webhook(request):
    """
    Webhook endpoint for Khalti payment notifications
    Khalti will send POST requests to this endpoint for payment events
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Log webhook data for debugging
            logger.info(f"Khalti Webhook Data: {data}")
            
            # Extract relevant information
            event_type = data.get('type')
            transaction_id = data.get('idx')
            
            # Find payment by transaction ID
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
                order = payment.order
                
                if event_type == 'COMPLETED':
                    # Update order status if not already updated
                    if order.status != 'PAID':
                        order.status = 'PAID'
                        order.save()
                        
                        # Create order update
                        update = OrderUpdate(
                            order=order,
                            update_desc=f"Payment confirmed via Khalti webhook. Transaction ID: {transaction_id}"
                        )
                        update.save()
                
                elif event_type == 'FAILED':
                    order.status = 'FAILED'
                    order.save()
                    
                    payment.payment_status = 'failed'
                    payment.save()
                    
                    update = OrderUpdate(
                        order=order,
                        update_desc=f"Payment failed. Transaction ID: {transaction_id}"
                    )
                    update.save()
                
                return JsonResponse({'success': True})
                
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for transaction ID: {transaction_id}")
                return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)
                
        except Exception as e:
            logger.exception(f"Webhook error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@login_required
def khalti_test_payment(request):
    """Test page for Khalti payment integration"""
    context = {
        'khalti_public_key': KHALTI_PUBLIC_KEY,
        'test_amount': 1000,  # Rs. 10 in paisa
    }
    return render(request, 'khalti_test.html', context)


# ==========================================
# ESEWA PAYMENT INTEGRATION
# ==========================================
@login_required
def esewa_payment(request):
    """eSewa payment initiation"""
    # Get order_id from GET parameter or session
    order_id = request.GET.get('order_id') or request.session.get('pending_order_id')
    
    if not order_id:
        messages.error(request, 'No pending order found')
        return redirect('checkout')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'amount': float(order.amount),
    }
    return render(request, 'esewa_payment.html', context)


@login_required
def esewa_success(request):
    """eSewa payment success callback"""
    if request.method == 'GET' or request.method == 'POST':
        # Get eSewa response parameters
        oid = request.GET.get('oid') or request.POST.get('oid')
        amt = request.GET.get('amt') or request.POST.get('amt')
        refId = request.GET.get('refId') or request.POST.get('refId')
        
        try:
            order = Order.objects.get(id=oid)
            
            # Update order status
            order.status = 'PAID'
            order.save()
            
            # Create payment record
            payment = Payment(
                order=order,
                payment_method='esewa',
                amount=Decimal(amt),
                payment_status='completed',
                transaction_id=refId,
                khalti_response={'refId': refId, 'amt': amt}
            )
            payment.save()
            
            # Create order update
            update = OrderUpdate(
                order=order,
                update_desc=f"Payment of Rs. {amt} completed via eSewa. Reference ID: {refId}"
            )
            update.save()
            
            # Clear session
            if 'pending_order_id' in request.session:
                del request.session['pending_order_id']
            
            messages.success(request, f'Payment successful! Order ID: {order.id}')
            return redirect('order_detail', order_id=order.id)
            
        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
            return redirect('index')
    
    return redirect('index')


@login_required
def esewa_failure(request):
    """eSewa payment failure callback"""
    order_id = request.session.get('pending_order_id')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'FAILED'
            order.save()
            
            # Create order update
            update = OrderUpdate(
                order=order,
                update_desc="Payment failed via eSewa"
            )
            update.save()
            
        except Order.DoesNotExist:
            pass
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('checkout')