---
name: payment-fraud-detector
description: >-
  Implement multi-layered fraud prevention using risk scoring, 3D Secure, velocity checks, and manual review queues to minimize chargebacks and protect revenue.
category: security-compliance
risk: critical
source: curated
date_added: "2026-03-12"
tags: [fraud, fraud-detection, 3ds, velocity-checks, stripe-radar, machine-learning, manual-review, chargeback]
triggers: ["fraud detection", "fraud prevention", "chargeback prevention", "3ds authentication", "velocity checks", "fraud scoring", "payment fraud"]
platforms: [shopify, woocommerce, bigcommerce, custom]
difficulty: advanced
---

# Detect and Prevent Payment Fraud

## Overview

Payment fraud costs ecommerce merchants 2–3% of revenue through lost goods, shipping costs, and dispute fees. Professional fraud prevention requires a multi-layered approach: platform-native risk scoring, payment-processor-level rules (e.g., Stripe Radar), real-time velocity checks, and a manual review process for high-value suspicious orders.

## When to Use This Skill

- When chargeback rates exceed **0.5%** of transaction volume.
- When launching in high-risk geographic markets or selling high-resale value goods (electronics, luxury items).
- When detecting "card testing" patterns (high volume of small-value failed transactions).
- When implementing a "Manual Review" queue to reduce false positives on large orders.
- When auditing a checkout flow to ensure compliance with 3D Secure (3DS) requirements.

## Core Instructions

### Step 1: Utilize Platform-Native Fraud Analysis

| Platform | Built-in Capabilities | Best Practice |
|----------|-----------------------|---------------|
| **Shopify** | Shopify Fraud Analysis (High/Medium/Low indicators). | Review indicators (CVV failure, IP/Billing mismatch) before fulfilling Medium/High risk orders. |
| **WooCommerce** | None (Relies on Processor). | Use Stripe or Braintree to leverage their built-in ML scoring and 3DS support. |
| **BigCommerce** | Processor-dependent. | Enable Advanced Fraud Tools in your payment gateway settings (e.g., PayPal Fraud Management). |
| **Enterprise** | Fraud Guarantee Services. | Consider services like Signifyd or NoFraud for "chargeback-proof" approvals (paid per transaction). |

### Step 2: Configure Payment-Level Rules (Stripe Radar)

If using a mainstream processor like Stripe, configure Radar rules to block or challenge suspicious transactions:

```text
# Block if the risk score from ML model is highest
Block if :risk_score: = 'highest'

# Require 3D Secure for large orders from new accounts
Review and Challenge (3DS) if :amount_in_usd: > 500 and :customer_account_age_days: < 7

# Block cards used more than 3 times in the last hour across different emails
Block if :card_velocity_hour: > 3
```

### Step 3: Implement Technical Guardrails (TypeScript)

For custom or headless architectures, use application-layer checks to catch patterns that generic ML models might miss.

#### Requesting 3D Secure Challenges
```typescript
const paymentIntent = await stripe.paymentIntents.create({
  amount: order.totalCents,
  currency: 'usd',
  payment_method_options: {
    card: {
      // Force 3DS challenge for high-risk scores to shift liability to the bank
      request_three_d_secure: riskScore > 75 ? 'challenge' : 'automatic',
    },
  },
});
```

#### Application-Layer Velocity Checks (Redis)
```typescript
async function checkVelocity(params: { email: string; ip: string; fingerprint: string; amount: number }) {
  // IP Velocity: Limit to 10 attempts per hour
  const ipCount = await redis.incr(`vel:ip:${params.ip}`);
  if (ipCount === 1) await redis.expire(`vel:ip:${params.ip}`, 3600);
  if (ipCount > 10) throw new Error('Velocity limit exceeded');

  // Spend Velocity: Limit to $1,000 per card fingerprint per 24h
  const dailySpend = await redis.incrby(`vel:spend:${params.fingerprint}`, params.amount);
  if (dailySpend > 100000) return { action: 'manual_review', reason: 'high_daily_spend' };

  return { action: 'allow' };
}
```

#### Manual Review Workflow
Always use **Authorize-then-Capture** for high-risk orders. Authorize the funds at checkout, then capture only after manual approval. Releasing an authorization is free; refunding a captured payment incurs transaction fee losses.

```typescript
async function processFraudReview(orderId: string, action: 'approve' | 'reject') {
  const order = await db.orders.findById(orderId);
  if (action === 'approve') {
    await stripe.paymentIntents.capture(order.paymentIntentId);
    await db.orders.update(orderId, { status: 'paid' });
  } else {
    await stripe.paymentIntents.cancel(order.paymentIntentId);
    await db.orders.update(orderId, { status: 'cancelled_fraud' });
  }
}
```

## Deepening: Fraud Patterns & Analytics

### Common Fraud Pattern Types
1. **Card Testing**: Fraudsters use bots to attempt hundreds of small transactions ($1-$5) to see which stolen cards are active. **Defense**: Implement Cloudflare Turnstile/CAPTCHA and IP-based rate limiting.
2. **Account Takeover (ATO)**: Compromised user credentials used to make purchases with saved cards. **Defense**: Alert users of logins from new IPs/Devices; require CVV even for saved cards.
3. **Triangulation Fraud**: A fraudster lists a product on a marketplace (eBay), waits for a real buyer, then uses a stolen card to buy the item from your store and ships it to the eBay buyer. **Defense**: Monitor for billing names that never match shipping names across multiple high-value orders.

### Chargeback Reason Code Analysis
Analyze your dispute history to refine your rules:
- **Fraudulent (Code 10.4)**: The actual owner didn't make the purchase. Solution: Stricter 3DS rules.
- **Product Not Received (Code 13.1)**: Customer claims it never arrived. Solution: Use signature-required shipping for high-value orders.
- **Significant Difference (Code 13.3)**: "Item not as described." Solution: Better product photography/descriptions.

### Device Fingerprinting
Look beyond IP and Email. Use browser signals (Screen resolution, Timezone, User-Agent, Installed fonts) to generate a unique "Device ID". If 10 different emails use the same Device ID to place orders in 1 hour, it is a bot attack.

## Best Practices & KPIs

- **Authorize-then-Capture**: Hold funds for up to 7 days for suspicious orders while you perform manual verification.
- **Chargeback Thresholds**:
    - **< 0.5%**: Healthy.
    - **0.6% - 0.9%**: Warning; optimize rules immediately.
    - **> 1.0%**: Excessive; high risk of being placed in the Visa/Mastercard Dispute Monitoring Program.
- **False Positive Rate**: Aim for < 1%. If you are blocking > 2% of total traffic, you are likely losing more in legitimate revenue than you are saving in fraud losses.
- **Deny-list Methodology**: Maintain a database of confirmed fraudulent emails, phone numbers, and shipping addresses. Block these globally before they reach the payment step.

