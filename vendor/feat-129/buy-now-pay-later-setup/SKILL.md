---
name: buy-now-pay-later-setup
description: >-
  Trigger: Add Klarna, Afterpay, or Affirm installment payments to checkout to increase AOV and reduce purchase hesitation.
category: payments-checkout
risk: critical
source: curated
date_added: "2026-03-12"
tags: [bnpl, klarna, afterpay, affirm, buy-now-pay-later, installments, financing]
platforms: [shopify, woocommerce, bigcommerce, custom]
difficulty: intermediate
---

# Add Buy Now, Pay Later (BNPL) to Checkout

## Overview

Buy Now, Pay Later (BNPL) allows shoppers to split their purchases into 4 interest-free installments or longer financing plans. Integrating BNPL directly into the checkout flow has been shown to increase **Average Order Value (AOV) by 15–40%** and reduce cart abandonment for higher-priced items. The primary industry providers are Klarna, Afterpay (Clearpay in the UK), and Affirm.

## When to Use This Skill

- When average order value (AOV) is in the $100–$3,000 range.
- When customers are dropping off at the payment step due to high ticket prices.
- When competitors in your category (fashion, electronics, furniture) already offer BNPL.
- When you want to leverage existing Stripe integrations to enable installment payments.

## Core Instructions

### Step 1: Provider Selection

Choose the provider that best fits your target market and typical order value:

| Provider | Markets | Model | Merchant Fee | Order Range |
|----------|---------|-------|--------------|-------------|
| **Klarna** | US, EU, UK | Pay in 4 / Financing | ~2.49% + $0.30 | $10–$10,000 |
| **Afterpay** | US, AU, UK, CA | Pay in 4 (6 weeks) | 4–6% | $35–$2,000 |
| **Affirm** | US, CA | Monthly installments | 5.99%–29.99% APR (Consumer) | $50–$17,500 |

*   **AOV Benchmarks:** 15-40% increase in AOV. 20-30% reduction in checkout abandonment for orders >$100.

### Step 2: Platform-Native Implementation

#### Shopify
Enable via **Shopify Payments** for the lowest integration effort:
1.  Go to **Settings → Payments → Shopify Payments → Manage**.
2.  Under **Wallets and payment methods**, find **Klarna** and **Afterpay** and toggle them on.
3.  Click **Save**. BNPL options will now appear automatically at checkout for eligible orders.

#### WooCommerce & BigCommerce
1.  Install the official provider plugin/app from the platform marketplace.
2.  Enter your API credentials (Merchant ID and Secret Key) from the provider's portal.
3.  Configure minimum and maximum order thresholds in the plugin settings to match the provider's eligibility range.

#### Custom / Headless (via Stripe)
If using Stripe, enable BNPL on the server side by adding the payment method types:

```javascript
// Server: Add Klarna and Afterpay to the payment intent
const paymentIntent = await stripe.paymentIntents.create({
  amount: orderTotalInCents,
  currency: 'usd',
  payment_method_types: ['card', 'klarna', 'afterpay_clearpay'],
  metadata: { order_id: orderId },
});
```

On the client, Stripe's `PaymentElement` will automatically render the appropriate BNPL tabs based on order eligibility.

### Step 3: On-Site Messaging

Visibility is key to increasing AOV. Do not wait until checkout to reveal BNPL options.
1.  **Product Pages:** Add a "4 interest-free payments of $X" widget beneath the price.
2.  **Cart Page:** Add a summary of installment options to reassure the customer before they enter the checkout flow.
3.  **Site-wide:** Mention "Pay in 4 with [Provider]" in the announcement bar.

### Step 4: Decision Criteria & Deepening

#### BNPL Compliance by Market
Each market has specific legal requirements for displaying BNPL terms. Ensure your on-site messaging uses the provider's approved disclosure text (e.g., "See terms" links). Failure to include these can lead to merchant account suspension.

#### Impact on Return Rates
BNPL can lead to higher return rates as customers feel less "sticker shock" during the purchase.
*   **Edge Case:** If your category already has high return rates (e.g., footwear), monitor if BNPL increases returns beyond your logistics capacity.
*   **Strategy:** Segment BNPL availability; consider disabling it for high-return items or specific "Final Sale" categories.

#### When NOT to Add BNPL
*   **Low Margin Items:** Afterpay's 6% fee can destroy profit on low-margin products. If your net margin is <15%, avoid high-fee BNPL providers.
*   **Subscriptions:** Some BNPL providers do not support recurring payments; check compatibility if your store relies on subscriptions.

## Best Practices

- **Zero-Friction Activation:** If on Shopify, use Shopify Payments rather than a standalone app to keep the checkout experience unified and fast.
- **Match the Tier:** Use Klarna/Afterpay for standard consumer goods and Affirm for high-ticket items ($1,000+) where long-term financing is required.
- **Test Eligibility Ranges:** Set your minimum order threshold (e.g., $50) slightly higher than your current AOV to encourage "cart padding."

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| BNPL not appearing at checkout | Verify the order total is within the provider's min/max range. Check that your API keys are in "Live" mode. |
| Price messaging is static | Ensure the product page widget updates its installment calculation when the customer selects different variants/prices. |
| High dispute rate | BNPL disputes follow the provider's rules. Ensure you have proof of delivery (tracking) for all BNPL-funded orders. |

