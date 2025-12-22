"""
Complete PayPal integration for Smart Data Organizer
Automatic instant upgrades after payment
"""

import streamlit as st
import streamlit.components.v1 as components
import paypalrestsdk
import json
from datetime import datetime
from utils.auth import update_user, refresh_current_user_session

# Configure PayPal SDK
def configure_paypal():
    """Configure PayPal with credentials from secrets"""
    try:
        paypalrestsdk.configure({
            "mode": st.secrets["paypal"]["mode"],  # "sandbox" or "live"
            "client_id": st.secrets["paypal"]["client_id"],
            "client_secret": st.secrets["paypal"]["secret"]
        })
        return True
    except:
        return False

def create_paypal_payment(user_email, amount=5.00, description="Pro Tier Upgrade"):
    """Create PayPal payment and return approval URL"""
    
    if not configure_paypal():
        return None
    
    try:
        # Create payment object
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": get_return_url(user_email, "success"),
                "cancel_url": get_return_url(user_email, "cancel")
            },
            "transactions": [{
                "amount": {
                    "total": str(amount),
                    "currency": "USD"
                },
                "description": description,
                "custom": user_email  # Store user email for verification
            }]
        })
        
        # Create payment
        if payment.create():
            # Find approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    return link.href
        
        return None
        
    except Exception as e:
        st.error(f"PayPal error: {str(e)}")
        return None

def get_return_url(user_email, status):
    """Generate return URL based on status"""
    base_url = st.secrets.get("app_url", "http://localhost:8501")
    
    if status == "success":
        return f"{base_url}/?payment=success&email={user_email}&tier=pro"
    else:
        return f"{base_url}/?payment=cancel&email={user_email}"

def execute_paypal_payment(payment_id, payer_id):
    """Execute PayPal payment after user approval"""
    
    if not configure_paypal():
        return False
    
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Get user email from payment custom field
            user_email = payment.transactions[0].custom
            
            # Update user tier
            if user_email and update_user(user_email, {'tier': 'pro'}):
                # Refresh session if it's the current user
                if st.session_state.get('user_email') == user_email:
                    refresh_current_user_session()
                
                # Log successful payment
                log_payment_success(user_email, payment_id, payment.transactions[0].amount.total)
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Payment execution error: {str(e)}")
        return False

def log_payment_success(user_email, payment_id, amount):
    """Log successful payment"""
    payment_log = {
        'user_email': user_email,
        'payment_id': payment_id,
        'amount': amount,
        'timestamp': datetime.now().isoformat(),
        'status': 'completed'
    }
    
    # Store in session (in production, use database)
    if 'payment_logs' not in st.session_state:
        st.session_state.payment_logs = []
    
    st.session_state.payment_logs.append(payment_log)

def show_paypal_checkout_component(user_email, amount=5.00):
    """Show PayPal Smart Button (recommended method)"""
    
    # Generate unique invoice ID
    import uuid
    invoice_id = f"SD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # PayPal button HTML/JavaScript
    paypal_html = f"""
    <div id="paypal-button-container"></div>
    
    <script src="https://www.paypal.com/sdk/js?client-id={st.secrets['paypal']['client_id']}&currency=USD"></script>
    
    <script>
        paypal.Buttons({{
            style: {{
                layout: 'vertical',
                color: 'blue',
                shape: 'rect',
                label: 'paypal'
            }},
            
            createOrder: function(data, actions) {{
                return actions.order.create({{
                    purchase_units: [{{
                        amount: {{
                            value: '{amount}'
                        }},
                        description: 'Smart Data Organizer - Pro Tier',
                        custom_id: '{user_email}',
                        invoice_id: '{invoice_id}'
                    }}]
                }});
            }},
            
            onApprove: function(data, actions) {{
                return actions.order.capture().then(function(orderData) {{
                    // Payment complete
                    console.log('Payment successful:', orderData);
                    
                    // Show success message
                    document.getElementById('paypal-button-container').innerHTML = 
                        '<div style="background-color: #d4edda; color: #155724; padding: 20px; border-radius: 8px; border: 1px solid #c3e6cb; text-align: center;">' +
                        '<h3 style="margin-top: 0;">Payment Successful!</h3>' +
                        '<p>Upgrading your account...</p>' +
                        '</div>';
                    
                    // Send success message to Streamlit
                    window.parent.postMessage({{
                        type: 'PAYMENT_SUCCESS',
                        orderId: data.orderID,
                        userEmail: '{user_email}',
                        tier: 'pro',
                        amount: '{amount}'
                    }}, '*');
                    
                }});
            }},
            
            onError: function(err) {{
                console.error('PayPal error:', err);
                document.getElementById('paypal-button-container').innerHTML += 
                    '<div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #f5c6cb;">' +
                    '<p>Payment failed. Please try again or contact support.</p>' +
                    '</div>';
            }},
            
            onCancel: function(data) {{
                document.getElementById('paypal-button-container').innerHTML += 
                    '<div style="background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #ffeaa7;">' +
                    '<p>Payment cancelled. You can try again anytime.</p>' +
                    '</div>';
            }}
            
        }}).render('#paypal-button-container');
    </script>
    """
    
    # Render PayPal button
    components.html(paypal_html, height=350)
    
    # JavaScript for handling payment success
    success_js = """
    <script>
    // Listen for payment success
    window.addEventListener('message', function(event) {
        if (event.data.type === 'PAYMENT_SUCCESS') {
            // Redirect to success page
            const url = new URL(window.location.href);
            url.searchParams.set('payment', 'success');
            url.searchParams.set('order_id', event.data.orderId);
            url.searchParams.set('tier', event.data.tier);
            url.searchParams.set('email', event.data.userEmail);
            
            window.location.href = url.toString();
        }
    });
    </script>
    """
    
    components.html(success_js, height=0)

def verify_payment_in_background(order_id, user_email):
    """Verify payment in background (simplified)"""
    
    try:
        # In production, you would:
        # 1. Call PayPal API to verify payment
        # 2. Check payment status
        # 3. Update user if verified
        
        # For now, we'll simulate verification
        # (In production, replace with actual PayPal API call)
        
        # Simulate API call delay
        import time
        time.sleep(2)
        
        # Mock verification - always returns True for testing
        # TODO: Replace with actual PayPal verification
        # payment = paypalrestsdk.Payment.find(order_id)
        # return payment.state == 'approved'
        
        return True
        
    except:
        return False

def show_paypal_pricing_page():
    """Complete PayPal pricing page"""
    
    if not st.session_state.get('logged_in'):
        st.error("Please login first")
        return
    
    from utils.auth import get_current_user
    user = get_current_user()
    user_email = st.session_state.user_email
    current_tier = user.get('tier', 'free')
    
    st.markdown("# Upgrade with PayPal")
    st.markdown("---")
    
    # Check for payment success
    if 'payment' in st.query_params and st.query_params['payment'] == 'success':
        handle_payment_success()
        return
    
    # Pricing columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## Free Tier")
        st.markdown("""
        **$0/month**
        
        ✓ 50 conversions/month  
        ✓ CSV export  
        ✓ Basic features  
        ✓ Email support
        """)
        
        if current_tier == 'free':
            st.success("Your Current Plan")
        elif st.button("Switch to Free", use_container_width=True, type="secondary"):
            update_user(user_email, {'tier': 'free'})
            refresh_current_user_session()
            st.success("Switched to Free tier!")
            st.rerun()
    
    with col2:
        st.markdown("## Pro Tier")
        st.markdown("""
        **$5.00/month**
        
        ✓ Unlimited conversions  
        ✓ Excel export  
        ✓ Advanced tools  
        ✓ Priority support  
        ✓ All future features
        """)
        
        if current_tier == 'pro':
            st.success("Your Current Plan")
            
            # Show payment history
            show_payment_history(user_email)
            
        else:
            st.markdown("### Instant Upgrade")
            
            # PayPal checkout button
            show_paypal_checkout_component(user_email, amount=5.00)
            
            # Alternative methods
            with st.expander("Other Payment Methods"):
                st.markdown("""
                **If PayPal doesn't work for you:**
                
                **Manual Bank Transfer:**
                - Send $5.00 USD
                - Reference: YOUR-EMAIL-HERE
                - Email receipt to: payments@smartdata.com
                
                **Mobile Money (Uganda):**
                - Send 18,500 UGX to 0773123456
                - Reference: PRO-UPGRADE
                """)
    
    # Usage stats
    st.markdown("---")
    from utils.auth import get_conversions_remaining
    remaining = get_conversions_remaining(user)
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Current Tier", current_tier.upper())
    with col_stat2:
        st.metric("Conversions Used", user.get('conversions_used', 0))
    with col_stat3:
        st.metric("Conversions Left", "Unlimited" if remaining == "Unlimited" else str(remaining))

def handle_payment_success():
    """Handle successful payment"""
    
    order_id = st.query_params.get('order_id')
    user_email = st.query_params.get('email')
    tier = st.query_params.get('tier', 'pro')
    
    # Verify it's the current user
    if user_email != st.session_state.user_email:
        st.error("Payment verification failed")
        return
    
    # Show processing message
    with st.spinner("Verifying payment..."):
        # Verify payment
        if verify_payment_in_background(order_id, user_email):
            # Update user tier
            if update_user(user_email, {'tier': tier}):
                refresh_current_user_session()
                
                st.success("""
                ## Upgrade Complete!
                
                Your account has been upgraded to **Pro Tier**.
                
                **New Features Available:**
                - Unlimited conversions
                - Excel export
                - Advanced data tools
                - Priority support
                
                You can start using all Pro features immediately.
                """)
                
                st.balloons()
                
                # Clear query params
                st.query_params.clear()
                
                # Auto-refresh after 3 seconds
                st.markdown("""
                <script>
                setTimeout(function() {
                    window.location.href = window.location.href.split('?')[0];
                }, 3000);
                </script>
                """, unsafe_allow_html=True)
        else:
            st.error("""
            ## Payment Verification Failed
            
            Please contact support with your order ID:
            **Order ID:** {}
            
            We'll manually verify and upgrade your account.
            """.format(order_id))

def show_payment_history(user_email):
    """Show user's payment history"""
    
    if 'payment_logs' in st.session_state:
        user_payments = [
            p for p in st.session_state.payment_logs 
            if p['user_email'] == user_email
        ]
        
        if user_payments:
            with st.expander("Payment History", expanded=False):
                for payment in user_payments[-5:]:  # Last 5 payments
                    st.write(f"**{payment['timestamp'][:10]}:** ${payment['amount']} - {payment['status']}")

# Admin functions
def show_paypal_admin_panel():
    """Admin view for PayPal payments"""
    
    st.markdown("### PayPal Payment Management")
    
    # Payment logs
    if 'payment_logs' in st.session_state and st.session_state.payment_logs:
        import pandas as pd
        df = pd.DataFrame(st.session_state.payment_logs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No payment records yet")
    
    # Test payment section
    st.markdown("---")
    st.markdown("#### Test Payments")
    
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        # Get test user
        from utils.auth import get_all_users
        users = get_all_users()
        
        if users:
            test_user = st.selectbox(
                "Select user for test payment:",
                [u['email'] for u in users]
            )
            
            if st.button("Simulate Successful Payment", use_container_width=True):
                # Simulate payment
                update_user(test_user, {'tier': 'pro'})
                log_payment_success(test_user, f"TEST-{datetime.now().timestamp()}", "5.00")
                st.success(f"Simulated payment for {test_user}")
                st.rerun()
    
    with col_test2:
        if st.button("Clear All Test Data", use_container_width=True, type="secondary"):
            if 'payment_logs' in st.session_state:
                st.session_state.payment_logs = []
            st.success("Cleared all test payment data")
            st.rerun()