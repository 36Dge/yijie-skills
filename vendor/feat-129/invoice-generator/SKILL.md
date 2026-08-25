---
name: invoice-generator
description: >-
  Automate the generation of tax-compliant, branded PDF invoices for B2B and B2C orders, ensuring sequential numbering and legal data retention.
category: payments-checkout
risk: safe
source: curated
date_added: "2026-03-12"
tags: [invoicing, billing, automation, vat-compliance, b2b-ecommerce]
triggers: ["invoice generation", "automated invoicing", "PDF invoice", "invoice automation", "billing automation", "generate invoice", "invoice template"]
platforms: [shopify, woocommerce, bigcommerce, custom]
difficulty: intermediate
---

# Automate Professional Invoice Generation

## Overview

Automated invoice generation turns every completed order into a professional, branded PDF document without manual effort. For B2B ecommerce and international markets (especially the EU), invoices are legal requirements for tax reclamation and procurement. A robust system ensures sequential numbering, tax-compliance fields, and immutable archival for audit purposes.

## When to Use This Skill

- When customers repeatedly request invoices for their accounting departments.
- When building B2B ecommerce workflows where net-terms or bank transfers require a formal "Request for Payment."
- When complying with EU VAT regulations that mandate specific invoice elements.
- When integrating storefront sales with professional accounting software (QuickBooks, Xero).
- When replacing payment processor "Receipts" with branded, legal "Invoices."

## Core Instructions

### Step 1: Platform-Native Invoicing Assessment

| Platform | Native Capability | Best Practice |
|----------|-------------------|---------------|
| **Shopify** | Order Confirmation Email | Use for B2C receipts; for legal PDF invoices, use a compliant invoicing app or a custom API. |
| **WooCommerce** | Email Notifications | Attach PDF invoices to "Order Completed" emails using a standard plugin; ensure sequential numbering is enabled. |
| **BigCommerce** | Order Confirmation PDF | Use the built-in Order Confirmation PDF for basic needs; customize the template for brand consistency. |
| **Custom / B2B** | Payment Processor API | Use **Stripe Invoicing** or a headless PDF generation engine for full control. |

### Step 2: Implementation Patterns (Technical Standards)

#### Pattern A: Stripe Invoicing (Mainstream/B2B)
Stripe Invoicing handles the complete lifecycle: creation, PDF generation, customer emailing, and payment tracking.

```javascript
// Create and finalize a Stripe Invoice for an order
const invoice = await stripe.invoices.create({
  customer: stripeCustomerId,
  collection_method: 'send_invoice', // or 'charge_automatically'
  days_until_due: 30,
  metadata: { order_id: orderId },
  custom_fields: [
    { name: 'PO Number', value: poNumber },
    { name: 'Buyer VAT ID', value: buyerVatNumber },
  ],
  footer: 'Tax Representative: [Your Company Name]',
});

// Add items to the invoice before finalization
for (const item of orderLines) {
  await stripe.invoiceItems.create({
    customer: stripeCustomerId,
    invoice: invoice.id,
    amount: item.totalCents,
    currency: 'usd',
    description: item.name,
    tax_rates: [taxRateId],
  });
}

// Finalize ensures the invoice is immutable and generates the PDF
await stripe.invoices.finalizeInvoice(invoice.id);
await stripe.invoices.sendInvoice(invoice.id);
```

#### Pattern B: Headless PDF Generation (Puppeteer/Handlebars)
For full design control on custom platforms, use a template-to-PDF pattern.

```javascript
// Generic pattern for server-side PDF generation
async function generateInvoicePdf(orderData: object) {
  const hb = require('handlebars');
  const puppeteer = require('puppeteer');

  // 1. Compile HTML from template
  const templateSource = fs.readFileSync('./templates/invoice.hbs', 'utf8');
  const template = hb.compile(templateSource);
  const html = template(orderData);

  // 2. Render to PDF using a headless browser
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });
  
  const pdfBuffer = await page.pdf({ 
    format: 'A4', 
    printBackground: true,
    margin: { top: '20px', bottom: '20px' } 
  });

  await browser.close();
  return pdfBuffer; // Save to S3 or email as attachment
}
```

### Step 3: EU VAT Mandatory Fields Checklist
Ensure your invoice template contains these 10 elements to remain legally compliant in the EU:

1. **Sequential Invoice Number**: Unique ID with no gaps (e.g., `INV-2026-0001`).
2. **Issue Date**: The date the invoice was generated.
3. **Seller Details**: Name, address, and VAT registration number.
4. **Buyer Details**: Name and billing address.
5. **Buyer VAT Number**: Required for B2B cross-border transactions within the EU.
6. **Description of Goods**: Itemized list with quantities.
7. **Unit Price**: Price per item excluding VAT.
8. **VAT Rate**: The percentage applied (e.g., 20%).
9. **VAT Amount**: Total tax amount for the order.
10. **Total Payable**: The final sum including all taxes.

## Deepening: Compliance & Operations

### Invoice vs. Receipt Distinction
- **Invoice**: A request for payment (pre-payment) or a legal tax record (post-payment). It is the primary document used by businesses to reclaim VAT/GST.
- **Receipt**: Proof that a payment was received. It does not necessarily contain the level of detail required for corporate tax filing.
- **Rule**: Always issue an *Invoice* for B2B orders, even if paid instantly via credit card.

### Sequential Numbering & Immutability
- **The Snapshot Principle**: When an invoice is generated, the customer's name and address must be "snapshotted" (copied) into the invoice record. If they change their address in their profile next year, the historical invoice must remain unchanged.
- **The Immutability Principle**: Never edit a finalized invoice. If a change is needed (e.g., a refund), do not delete the invoice.
- **Credit Note Process**: Issue a "Credit Note" (a negative invoice) that references the original invoice number. This maintains the accounting audit trail required by law.

### Archival Requirements
Many jurisdictions (e.g., Germany - GoBD, France) require invoices to be archived in an unalterable format (WORM - Write Once, Read Many) for **6 to 10 years**. Ensure your storage solution (e.g., AWS S3 with Object Lock or a dedicated document management system) supports these retention policies.

## Best Practices

- **Payment Link Prominence**: For unpaid invoices (Net-30), the "Pay Now" link or bank transfer instructions should be the most visible element on the page.
- **Automatic Sync**: Automate the pushing of invoices to your accounting platform (Xero/QuickBooks) the moment the invoice is finalized to ensure real-time financial reporting.
- **Dunning Automation**: For B2B orders, set up automated reminders 3 days before, on the day, and 7 days after the due date for any unpaid invoices.

## Common Pitfalls

| Problem | Root Cause / Solution |
|---------|----------|
| **Numbering Gaps** | Using Order IDs as Invoice IDs (Order #105 might fail, leaving a gap). **Solution**: Use a separate sequential counter for Invoices only. |
| **Tax Miscalculation** | Not accounting for tax-on-shipping. **Solution**: Explicitly list shipping as a line item and apply the relevant tax rate. |
| **Missing "Reverse Charge"** | Cross-border B2B sales in the EU. **Solution**: If the buyer provides a valid VAT ID, the invoice must state "VAT Reverse Charge" and show 0% tax. |
| **Unreadable PDFs** | Too many images or complex CSS. **Solution**: Use a standard system font and SVG logos to keep PDF file sizes small (< 200KB) for email delivery. |

