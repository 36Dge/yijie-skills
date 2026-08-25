---
name: multichannel-inventory-sync
description: >-
  Establish a single source of truth for inventory and orders across Shopify, Amazon, eBay, and social commerce channels to prevent overselling
category: business-operations
risk: critical
source: curated
date_added: "2026-03-12"
tags: [multi-channel, omnichannel, catalog-sync, inventory-sync, marketplace, wholesale, DTC]
triggers: ["multi-channel selling", "omnichannel inventory", "channel sync", "marketplace integration", "unified catalog", "cross-channel inventory"]
tools: [claude-code, cursor, gemini-cli, copilot, codex-cli, kiro, opencode]
platforms: [shopify, woocommerce, bigcommerce, custom]
difficulty: advanced
---

# Sync Inventory Across Multi-Channel Marketplaces

## Overview

Multi-channel selling allows merchants to list products on their own website, Amazon, eBay, Walmart, and social platforms simultaneously. The critical operational requirement is **atomic inventory synchronization**: every sale on any channel must immediately decrement the available stock across all other channels to prevent overselling. This requires a central "master" inventory system, typically the e-commerce platform's admin or a specialized Order Management System (OMS).

## When to Use This Skill

- When expanding a DTC brand into marketplaces like Amazon or eBay.
- When inventory levels are low and the risk of overselling on a fast-moving channel is high.
- When managing both a retail storefront and a B2B/Wholesale portal from a single warehouse.
- When consolidating multiple brand storefronts into a unified backend fulfillment process.

## Core Instructions

### Step 1: Prepare the Primary Store as Inventory Master

Before connecting external channels, ensure the following data is accurate in your primary platform (Shopify, WooCommerce, or BigCommerce):
- **Accurate Stock Levels**: Physical count must match the digital record.
- **UPC/GTIN Barcodes**: Required for Amazon, Walmart, and Google Shopping listings.
- **Product Dimensions/Weights**: Essential for accurate shipping rate calculation on marketplaces.
- **HS Codes**: Necessary for international marketplace sales (cross-border).

### Step 2: Connect Platform-Native Sales Channels

#### Shopify Admin
1. Navigate to **Settings → Sales channels**.
2. Add the **Facebook & Instagram** channel (Meta's official integration) to sync your product catalog to Facebook Shop and Instagram Shopping.
3. Add the **Google & YouTube** channel to enable Google Shopping and Buy on Google.
4. For Amazon/eBay, use the **Marketplace Connect** app (Shopify's native solution) to link your Seller Central accounts.

#### BigCommerce Channel Manager
1. Go to **Channel Manager** in the side navigation.
2. Select **Marketplaces** to connect to Amazon and eBay.
3. Select **Social** to link to Meta (Facebook/Instagram) and TikTok Shop.
4. Use the native field mapping to ensure BigCommerce product attributes align with marketplace requirements.

#### WooCommerce
1. Use your WooCommerce dashboard as the central hub.
2. For marketplace connections, install reputable channel-specific plugins that support real-time inventory hooks.
3. Ensure the `woocommerce_product_set_stock` hook is correctly firing to trigger updates to external APIs.

### Step 3: Configure Marketplace Requirements

#### Amazon Seller Central
- **Account Level**: Requires a **Professional Seller** account ($39.99/mo).
- **GTIN Requirement**: Amazon strictly enforces GS1-compliant barcodes. Apply for a GTIN exemption only for private label/handmade goods.
- **Fulfillment Latency**: Set "Handling Time" accurately. Amazon requires tracking numbers within 48 hours of the ship-by date to maintain account health.

#### Walmart Marketplace
- **Approval**: Requires application and verification of business credentials.
- **Image Standards**: Strict adherence to white background (RGB 255, 255, 255) for primary images.

### Step 4: Implement Atomic Order Ingestion (Technical)

For custom integrations, normalize marketplace orders into a standard internal format and use database transactions to reserve inventory.

```typescript
// Normalize an order from any marketplace into a common format
interface NormalizedMarketplaceOrder {
  channelName: string;       // 'amazon', 'ebay', 'walmart', 'shopify'
  channelOrderId: string;    // the marketplace's order ID
  lines: {
    masterSku: string;       // your internal central SKU
    quantity: number;
    unitPriceCents: number;
  }[];
  shippingAddress: object;
}

async function ingestMarketplaceOrder(order: NormalizedMarketplaceOrder): Promise<void> {
  // Idempotency: Skip if already imported to prevent duplicates from webhook retries
  const existing = await db.orders.findByChannelOrderId(order.channelName, order.channelOrderId);
  if (existing) return;

  await db.transaction(async tx => {
    // 1. Create the order in your internal system
    const createdOrder = await tx.orders.insert({
      channel: order.channelName,
      channel_order_id: order.channelOrderId,
      status: 'awaiting_fulfillment',
      shipping_address: order.shippingAddress,
    });

    // 2. Atomic Inventory Reservation
    for (const line of order.lines) {
      // Use a WHERE clause to ensure we don't oversell in a race condition
      const result = await tx.raw(`
        UPDATE inventory 
        SET reserved = reserved + ?,
            available = available - ?
        WHERE sku = ? AND available >= ?
      `, [line.quantity, line.quantity, line.masterSku, line.quantity]);

      if (result.rowCount === 0) {
        throw new Error(`Inventory stockout for SKU ${line.masterSku} during ${order.channelName} ingestion`);
      }
    }
  });
}
```

## Decision Criteria & Deep Analysis

### Channel Economics Framework
Do not sell on every channel. Evaluate each using the **Contribution Margin** per channel:
`Net Profit = Revenue - (COGS + Marketplace % Fee + Fixed Listing Fee + Shipping Cost + Return Processing Cost)`
- **Amazon**: High volume, high fees (15% avg), high return rates.
- **eBay**: Good for refurbished/long-tail, lower fees, lower traffic.
- **Shopify/DTC**: Highest margin, but requires independent marketing spend (CAC).
- **Strategy**: If a product has a margin <15% after shipping, avoid high-fee marketplaces.

### Listing Quality Score (LQS)
Ranking on marketplaces is driven by LQS. Optimization targets:
- **Title Density**: 150-200 characters including high-volume keywords.
- **Image Quantity**: Minimum 7 images + 1 video.
- **Review Velocity**: Amazon "Buy Box" is heavily weighted by the number of reviews received in the last 30 days.

### Multi-Currency Pricing Strategy
When selling on international marketplaces (e.g., Amazon.co.uk from a US store):
- **Fixed vs. Dynamic**: Don't just use daily exchange rates. Set fixed prices per region (e.g., $29.99 vs £24.99) to account for different VAT/GST requirements and local shipping costs.

## Best Practices

- **Safety Stock Buffer**: Set a "Buffer Quantity" (e.g., 2 units) for marketplaces. If your real stock is 2, the system tells Amazon it is 0. This protects your site's stock from a sudden marketplace surge.
- **Atomic Inventory Master**: Only one system should be the "source of truth." Never allow two systems to both try to "master" inventory levels.
- **SKU Mapping**: Use a "Channel SKU" to "Master SKU" mapping table. Marketplace SKUs often differ from internal warehouse SKUs.
- **2-Day Amazon Sync**: Ensure your integration pushes tracking numbers back to Amazon within 48 hours. Failing this is the #1 cause of marketplace account suspension.

## Common Pitfalls & Edge Cases

| Problem | Solution |
|---------|----------|
| **Overselling (Race Condition)** | Use database-level row locking (`SELECT FOR UPDATE`) or atomic decrement queries during order ingestion. |
| **Pricing Parity Violations** | Amazon may delist products if they find the same item significantly cheaper on your own site. Monitor "Price Health" in Seller Central. |
| **Duplicate Imports** | Ensure your order ingestion logic is idempotent using the `channel_order_id` as a unique key. |
| **Bundle Breakdown** | If selling a "3-Pack" as a separate SKU, ensure the system decrements 3 units of the "Single" SKU master inventory. |

