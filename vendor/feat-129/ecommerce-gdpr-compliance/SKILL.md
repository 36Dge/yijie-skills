---
name: ecommerce-gdpr-compliance
description: >-
  Implement GDPR compliance for ecommerce including cookie consent, Subject Access Requests (SAR), right to erasure, and data processing agreements.
---

# Implement GDPR Compliance for Ecommerce

## Overview

The General Data Protection Regulation (GDPR) applies to any ecommerce business serving customers in the European Union (EU) or the European Economic Area (EEA), regardless of where the business is headquartered. Following Brexit, the **UK GDPR** creates an equivalent requirement for customers in the United Kingdom.

Non-compliance carries severe financial and reputational risks, with fines up to **€20M or 4% of global annual turnover**. Compliance is built on four pillars: Informed Consent, Data Portability (SAR), the Right to Erasure, and Lawful Basis for processing.

## ⚠️ Safety Constraint

This skill is for **informational guidance only**. The agent MUST NOT use browser, bash, or any other tool to directly access, modify, anonymize, or delete customer data on any platform (Shopify, WooCommerce, etc.). All data operations must be performed manually by the user.

## When to Use This Skill

- When launching a store or marketing campaign targeting EU, EEA, or UK customers.
- When adding new tracking pixels (Meta, TikTok, Google) or third-party apps that process customer data.
- When a customer submits a formal request to access or delete their personal data.
- When auditing your vendor list for required Data Processing Agreements (DPAs).

## 1. Register of Processing Activities (RoPA)

Under Article 30, you must maintain a record of why and how you process personal data. Use this framework to map your store's data:

| Data Category | Lawful Basis | Retention Period | Example |
|---------------|--------------|------------------|---------|
| **Order Data** | Contract (Art. 6(1)(b)) | 7 Years (Tax/Legal) | Name, Shipping Address, Items. |
| **Account Data** | Contract | Until Deletion + 30 Days | Email, Password Hash, Order History. |
| **Marketing** | Consent (Art. 6(1)(a)) | Until Unsubscribe | Email for Newsletters, SMS. |
| **Analytics** | Consent | 13–26 Months | Page Views, Device Type, Referrer. |
| **Security** | Legitimate Interest | 90 Days | IP Address, Fraud Scores. |

## 2. Consent Management & Analytics

Consent must be **freely given, specific, informed, and unambiguous**.

### The Cookie Banner Rule
- **No Pre-ticked Boxes**: All non-essential categories (Analytics, Marketing) must be "OFF" by default.
- **Granularity**: Users must be able to accept "Necessary" cookies while rejecting "Marketing" cookies.
- **Withdrawal**: Withdrawing consent must be as easy as giving it (e.g., a visible "Privacy Settings" link in the footer).

### Platform-Native Implementations
- **Shopify**: Use the native **Privacy & Compliance** settings to enable the consent banner and link it to the **Shopify Customer Privacy API**. This ensures that Google and Meta pixels only fire *after* the user clicks "Accept."
- **WooCommerce**: Use the built-in Privacy settings (**Settings → Privacy**) to link your Privacy Policy. Use **Google Analytics Consent Mode** to adjust tag behavior based on user choice.
- **Google Analytics (GA4)**: Enable "Consent Mode" to allow Google to model data for users who opt out of cookies while remaining compliant.

## 3. Subject Access Requests (SAR)

Under Article 20, customers have a right to a machine-readable copy of their data.

- **The Window**: You must respond within **30 days**.
- **The Process (Shopify)**: In the Customer Profile, use the **"Request Data"** button. Shopify will generate an export and email it to the customer.
- **The Process (WooCommerce)**: Navigate to **Tools → Export Personal Data**. Enter the email, send a confirmation link, and then generate the ZIP export.
- **Verification**: Always verify the requester's identity (usually via a confirmation email to the address on file) before releasing data.

## 4. Right to Erasure (Article 17)

The "Right to be Forgotten" allows customers to request the deletion of their data, but it is not absolute.

### Anonymization vs. Deletion
- **Critical Distinction**: You cannot delete order records required for tax and accounting purposes. Instead, you must **anonymize** them.
- **Action**: Replace the customer's Name, Email, and Phone Number with a placeholder (e.g., "Deleted User") while preserving the financial transaction data.
- **Implementation**: 
    - **Shopify**: Use "Erase Personal Data" in the customer profile. Shopify will redact PII and notify installed apps via webhook.
    - **WooCommerce**: Use **Tools → Erase Personal Data**. This anonymizes the customer account and associated orders.

## 5. Data Processing Agreements (DPA)

You are the "Data Controller." Any service you use is a "Data Processor." You must have a signed DPA with every processor:
- **Payment Processors**: Stripe, PayPal, Adyen.
- **Email/SMS**: Klaviyo, Mailchimp, Omnisend.
- **Hosting/Platform**: Shopify, BigCommerce, AWS.
- **Analytics**: Google, Hotjar.

*Most major vendors include a DPA in their standard Terms of Service; ensure you have "accepted" the specific DPA addendum in your account settings.*

## Deepening: Global Privacy Overlap

### GDPR vs. UK GDPR
Since Brexit, these are two separate laws. While they are currently aligned, you must reference both in your Privacy Policy if you serve both regions. Use a single "Privacy Center" to handle requests for both.

### CCPA / CPRA (California) Overlap
GDPR is stricter than CCPA. If you are GDPR-compliant, you meet ~90% of CCPA requirements. Key differences: CCPA requires a specific "Do Not Sell or Share My Personal Information" link if you use data for targeted advertising.

## New Store Launch Checklist

1.  [ ] **Privacy Policy**: Explicitly list all third-party "Processors" (apps/pixels).
2.  [ ] **Consent Banner**: Set to "Opt-in" (not Opt-out) for EU/UK traffic.
3.  [ ] **Checkout Opt-in**: Marketing checkbox must be **unchecked** by default.
4.  [ ] **Data Request Email**: Create a dedicated inbox (e.g., `privacy@yourbrand.com`) to receive SARs.
5.  [ ] **App Audit**: Remove any unused apps that have "Read Customer" permissions.

