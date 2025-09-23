# Khalti Test / Sandbox Credentials
KHALTI_SECRET_KEY = "test_secret_key_from_merchant_dashboard"
# ↑  You get this when you create a merchant account and enable sandbox.
#    Use it as:  Authorization: Key <KHALTI_SECRET_KEY>

# API Endpoints (sandbox)
KHALTI_INIT_URL   = "https://a.khalti.com/api/v2/epayment/initiate/"
KHALTI_LOOKUP_URL = "https://a.khalti.com/api/v2/epayment/lookup/"

# Test Khalti User credentials (for logging in on the payment page)
TEST_USER_NUMBER   = "9800000000"   # you can also use 9800000001 … 9800000005
TEST_USER_MPIN     = "1111"        # MPIN for sandbox users
TEST_USER_OTP      = "987654"      # OTP for sandbox login

# Example purchase/order info used when initiating a payment
# (These values are supplied dynamically by your code)
# PURCHASE_ORDER_ID   = "<your_order_id>"
# PURCHASE_ORDER_NAME = "Order <your_order_id>"
# AMOUNT_IN_PAISA     = <amount_in_paisa>
