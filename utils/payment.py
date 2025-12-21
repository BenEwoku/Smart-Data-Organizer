# File: utils/payment.py
"""
Payment processing and subscription management
Uses Stripe for payment processing
"""

import streamlit as st

# Pricing configuration
PRICING_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'conversions': 5,
        'features': [
            '5 conversions per month',
            'Basic text parsing',
            'Web scraping (3 URLs/month)',
            'CSV export',
            'Email support'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 19.99,
        'conversions': 'unlimited',
        'features': [
            '✨ Unlimited conversions',
            'All export formats (CSV, Excel, JSON)',
            'Advanced web scraping',
            'Batch processing (10 files)',
            'Structure-specific tools',
            'Save templates (10)',
            'Priority email support'
        ],
        'stripe_price_id': 'price_pro_monthly'  # Replace with actual Stripe Price ID
    },
    'analyst': {
        'name': 'Analyst',
        'price': 39.99,
        'conversions': 'unlimited',
        'features': [
            '✨ Everything in Pro',
            'OCR for images/PDFs',
            'Advanced panel data tools',
            'Time series analysis',
            'API access (1000 calls/month)',
            'Scheduled scraping (10 jobs)',
            'Save 50 templates',
            'Priority support + chat'
        ],
        'stripe_price_id': 'price_analyst_monthly'  # Replace with actual Stripe Price ID
    },
    'business': {
        'name': 'Business',
        'price': 99.99,
        'conversions': 'unlimited',
        'features': [
            '✨ Everything in Analyst',
            'Team collaboration (5 users)',
            'Unlimited API calls',
            'White-label exports',
            'Custom integrations',
            'Webhook support',
            'Dedicated account manager',
            '24/7 priority support'
        ],
        'stripe_price_id': 'price_business_monthly'  # Replace with actual Stripe Price ID
    }
}

def show_pricing_page():
    """Display pricing tiers and upgrade options"""
    st.markdown("## 💳 Choose Your Plan")
    st.markdown("Select the plan that best fits your needs")
    
    # Create columns for pricing cards
    cols = st.columns(4)
    
    for idx, (tier_id, tier) in enumerate(PRICING_TIERS.items()):
        with cols[idx]:
            # Highlight current tier
            is_current = False
            if st.session_state.get('logged_in'):
                user = st.session_state.user_data
                is_current = (user['tier'] == tier_id)
            
            # Card styling
            if is_current:
                st.success(f"**Current Plan**")
            
            st.markdown(f"### {tier['name']}")
            
            # Price
            if tier['price'] == 0:
                st.markdown("## FREE")
            else:
                st.markdown(f"## ${tier['price']}")
                st.caption("per month")
            
            # Features
            st.markdown("---")
            for feature in tier['features']:
                st.markdown(f"✓ {feature}")
            
            st.markdown("---")
            
            # CTA Button
            if tier_id == 'free':
                if not st.session_state.get('logged_in'):
                    if st.button("Get Started", key=f"btn_{tier_id}", use_container_width=True):
                        st.info("Please sign up to get started")
                else:
                    st.button("Current Plan", key=f"btn_{tier_id}", disabled=True, use_container_width=True)
            else:
                if st.session_state.get('logged_in'):
                    if is_current:
                        st.button("Current Plan", key=f"btn_{tier_id}", disabled=True, use_container_width=True)
                    else:
                        if st.button(f"Upgrade to {tier['name']}", key=f"btn_{tier_id}", type="primary", use_container_width=True):
                            show_stripe_checkout(tier_id, tier)
                else:
                    if st.button("Sign Up First", key=f"btn_{tier_id}", use_container_width=True):
                        st.info("Please create an account first")

def show_stripe_checkout(tier_id, tier):
    """Show Stripe payment checkout"""
    st.markdown("### 💳 Checkout")
    
    # In production, this would redirect to Stripe Checkout
    # For now, show a simulated checkout
    
    st.info(f"""
    **Upgrading to {tier['name']} Plan**
    
    Price: ${tier['price']}/month
    
    In production, this would redirect to Stripe Checkout.
    
    **For now, click 'Simulate Payment' to test the upgrade:**
    """)
    
    if st.button("🎭 Simulate Payment (Demo)", type="primary"):
        # Simulate successful payment
        simulate_successful_payment(tier_id)

def simulate_successful_payment(tier_id):
    """Simulate a successful payment (for demo purposes)"""
    if st.session_state.get('logged_in'):
        from utils.auth import update_user_tier
        
        email = st.session_state.user_email
        update_user_tier(email, tier_id)
        
        st.success(f"✅ Payment successful! Upgraded to {PRICING_TIERS[tier_id]['name']} tier")
        st.balloons()
        st.rerun()

def create_stripe_checkout_session(tier_id, user_email):
    """
    Create Stripe checkout session (Production implementation)
    
    This is placeholder code - in production, you would:
    1. Install stripe: pip install stripe
    2. Set up Stripe API keys in secrets
    3. Create actual checkout session
    """
    
    # Production code would look like:
    """
    import stripe
    
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    
    checkout_session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=['card'],
        line_items=[{
            'price': PRICING_TIERS[tier_id]['stripe_price_id'],
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://yourapp.streamlit.app/?success=true',
        cancel_url='https://yourapp.streamlit.app/?canceled=true',
    )
    
    return checkout_session.url
    """
    
    # For now, return demo URL
    return "https://checkout.stripe.com/demo"

def handle_stripe_webhook(payload, sig_header):
    """
    Handle Stripe webhooks for payment events
    
    In production, this would:
    1. Verify webhook signature
    2. Handle events: payment_intent.succeeded, customer.subscription.deleted, etc.
    3. Update user tier accordingly
    """
    pass

def show_billing_portal():
    """Show user's billing information and manage subscription"""
    if not st.session_state.get('logged_in'):
        st.warning("Please login to view billing")
        return
    
    user = st.session_state.user_data
    tier = user['tier']
    
    st.markdown("## 💳 Billing & Subscription")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Current Plan")
        tier_info = PRICING_TIERS[tier]
        st.info(f"""
        **Plan:** {tier_info['name']}
        
        **Price:** ${tier_info['price']}/month
        
        **Conversions:** {tier_info['conversions']}
        """)
        
        if tier != 'free':
            st.markdown("**Next billing date:** January 21, 2026")
    
    with col2:
        st.markdown("### Usage This Month")
        conversions_used = user.get('conversions_used', 0)
        st.metric("Conversions Used", conversions_used)
        
        if tier == 'free':
            remaining = max(0, 5 - conversions_used)
            st.metric("Remaining", f"{remaining}/5")
        else:
            st.metric("Remaining", "Unlimited ♾️")
    
    st.markdown("---")
    
    # Upgrade/Downgrade options
    col1, col2 = st.columns(2)
    
    with col1:
        if tier != 'business':
            if st.button("⬆️ Upgrade Plan", type="primary", use_container_width=True):
                st.session_state.show_pricing = True
                st.rerun()
    
    with col2:
        if tier != 'free':
            if st.button("⬇️ Cancel Subscription", use_container_width=True):
                if st.checkbox("I want to cancel my subscription"):
                    if st.button("Confirm Cancellation", type="secondary"):
                        from utils.auth import update_user_tier
                        update_user_tier(st.session_state.user_email, 'free')
                        st.success("Subscription canceled. Downgraded to Free tier.")
                        st.rerun()
    
    # Payment history
    with st.expander("📜 Payment History"):
        st.markdown("""
        | Date | Amount | Status |
        |------|--------|--------|
        | Dec 21, 2024 | $19.99 | Paid ✅ |
        | Nov 21, 2024 | $19.99 | Paid ✅ |
        | Oct 21, 2024 | $19.99 | Paid ✅ |
        
        *Demo data - In production, this would show real payment history from Stripe*
        """)

def check_feature_access(feature_name):
    """
    Check if user has access to a specific feature
    
    Args:
        feature_name: Name of feature to check
        
    Returns:
        bool: True if user has access
    """
    if not st.session_state.get('logged_in'):
        return False
    
    user = st.session_state.user_data
    tier = user['tier']
    
    # Feature access matrix
    feature_tiers = {
        'batch_processing': ['pro', 'analyst', 'business'],
        'api_access': ['analyst', 'business'],
        'scheduled_scraping': ['analyst', 'business'],
        'ocr': ['analyst', 'business'],
        'team_features': ['business'],
        'white_label': ['business']
    }
    
    required_tiers = feature_tiers.get(feature_name, [])
    return tier in required_tiers

def show_upgrade_prompt(feature_name, required_tier):
    """Show prompt to upgrade for a feature"""
    st.warning(f"""
    ⭐ This feature requires {PRICING_TIERS[required_tier]['name']} plan or higher.
    
    Upgrade now to unlock this feature!
    """)
    
    if st.button("View Pricing", type="primary"):
        st.session_state.show_pricing = True
        st.rerun()