# saas_service_mappings.py
# Industry-aligned multipliers for SaaS subscription and lead generation datasets
# Based on SaaS benchmarks (OpenView, SaaS Capital, KeyBanc, public SaaS S-1s)

# Subscription plan revenue multipliers (relative to Free)
PLAN_REVENUE_MULTIPLIER = {
    'Free': 0.01,        # Free users: many, but negligible revenue
    'Basic': 1,         # Basic: entry-level, low ARPU
    'Pro': 3,           # Pro: mid-market, higher ARPU
    'Enterprise': 10,   # Enterprise: fewest, but highest ARPU
}

# Usage event multiplier (simulate higher usage for paid plans)
PLAN_USAGE_MULTIPLIER = {
    'Free': 0.5,
    'Basic': 1,
    'Pro': 2,
    'Enterprise': 3,
}

# Lead generation: annual revenue and employee count scaling by industry (example)
INDUSTRY_REVENUE_MULTIPLIER = {
    'Consumer Electronics': 1.2,
    'Automotive': 1.5,
    'Food & Beverage': 0.8,
    'Toys': 0.6,
    'Medical Devices': 1.3,
    'Apparel': 0.7,
    'Home Goods': 0.9,
    'Industrial Equipment': 1.1,
}

# Engagement status close rates (for demo/CRM realism)
ENGAGEMENT_CLOSE_RATE = {
    'Not Contacted': 0.0,
    'Attempted': 0.01,
    'Engaged': 0.05,
    'Demo Scheduled': 0.15,
    'Closed Won': 1.0,
    'Closed Lost': 0.0,
}
