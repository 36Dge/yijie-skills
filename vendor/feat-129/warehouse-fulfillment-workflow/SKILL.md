---
name: warehouse-fulfillment-workflow
description: >-
  Optimize warehouse operations with digital pick lists, packing station workflows, and carrier-agnostic label generation to increase fulfillment speed and accuracy
category: fulfillment-shipping
risk: critical
source: curated
date_added: "2026-03-12"
tags: [fulfillment, pick-pack-ship, warehouse, barcode-scanning, packing-slip, wms]
triggers: ["order fulfillment", "pick pack ship", "warehouse workflow", "packing slip", "barcode scanning fulfillment", "warehouse management"]
tools: [claude-code, cursor, gemini-cli, copilot, codex-cli, kiro, opencode]
platforms: [shopify, woocommerce, bigcommerce, custom]
difficulty: intermediate
---

# Design Warehouse Pick-Pack-Ship Workflow

## Overview

A warehouse fulfillment workflow transforms a digital order into a physical shipment. The objective is to maximize "orders per hour" while maintaining a pick accuracy rate of >99.5%. This is achieved through three distinct phases: **Picking** (retrieving items from shelves), **Packing** (verifying items and choosing boxes), and **Shipping** (generating carrier labels and manifest).

## When to Use This Skill

- When transitioning from a manual, paper-based fulfillment process to a digital system.
- When expanding to multiple warehouse locations or using a 3PL.
- When mis-ships (wrong items sent) exceed 0.5% of total orders.
- When warehouse labor costs are rising due to inefficient picker routing.

## Core Instructions

### Step 1: Implement Platform-Native Fulfillment

#### Shopify Admin
1. Navigate to **Orders** and select "Unfulfilled" orders.
2. **Bulk Picking**: Select multiple orders → **Print → Packing slips**. Shopify generates a combined document for floor use.
3. **Fulfillment**: Click **Fulfill items**. Choose between:
   - **Shopify Shipping**: Buy discounted labels from USPS, UPS, or DHL directly.
   - **Manual Fulfillment**: Enter tracking numbers from an external carrier.
4. **SFN (Shopify Fulfillment Network)**: If using Shopify's 3PL, orders are automatically routed to the nearest node for fulfillment without merchant intervention.

#### WooCommerce Admin
1. Go to **WooCommerce → Orders**.
2. **Packing Slips**: Select orders → **Bulk actions → Print PDF Packing Slips** (requires native WooCommerce PDF extension).
3. **Fulfillment**: Use the **WooCommerce Shipping** extension to print labels directly from the order detail page.
4. Mark orders as "Completed" to trigger the automated shipping confirmation email with tracking details.

#### BigCommerce Admin
1. Navigate to **Orders → View**.
2. Use the **Ship Items** button to select line items and quantities for a specific shipment.
3. Print **Packing Slips** and **Invoices** directly from the "Print" dropdown in the order list.

### Step 2: Technical Workflow Integration (Custom/API)

For custom Warehouse Management Systems (WMS), use a carrier-agnostic API pattern to generate labels and update order status.

```typescript
/**
 * Generic Carrier API implementation for label generation
 */
async function generateCarrierLabel(params: {
  warehouseAddress: Address;
  customerAddress: Address;
  parcelData: Parcel;
  carrierCode: string; // e.g., 'ups', 'fedex', 'usps'
}): Promise<{ trackingNumber: string; labelPdfUrl: string }> {
  
  // 1. Initialize carrier-agnostic client
  const client = new CarrierClient(process.env.CARRIER_API_KEY);

  // 2. Create shipment object
  const shipment = await client.shipment.create({
    from: params.warehouseAddress,
    to: params.customerAddress,
    parcels: [params.parcelData]
  });

  // 3. Purchase the most economical rate for the selected carrier
  const bestRate = shipment.rates
    .filter(r => r.carrier === params.carrierCode)
    .sort((a, b) => a.price - b.price)[0];

  const transaction = await client.transaction.create({
    rateId: bestRate.id,
    labelFormat: 'PDF_4x6'
  });

  return {
    trackingNumber: transaction.trackingNumber,
    labelPdfUrl: transaction.labelUrl
  };
}
```

## Decision Criteria & Industry Benchmarks

### Picking Strategy Efficiency
- **Single-Order Picking**: Best for large, heavy items or low-volume stores.
- **Batch Picking**: Best for small items. Pickers retrieve items for 10-20 orders simultaneously. **Benchmark**: Batch picking typically increases efficiency by **30–50%** over single-order picking.
- **Zone Picking**: Pickers stay in assigned aisles and items are consolidated at a "pack station." Necessary for warehouses >20,000 sq. ft.

### Warehouse Zone Design
Inventory should be placed based on velocity (Sales Frequency):
- **Hot Zone**: Place the top 10-20% of SKUs (the ones that account for 80% of sales) nearest to the packing stations.
- **Cold Zone**: Place low-velocity, seasonal, or oversized items at the back of the warehouse.
- **Benchmark**: Sorting pick lists by **Bin Location** (aisle → shelf → bin) reduces pick time by **15–25%**.

### Quality Control (QC) Checkpoints
Mis-ships are expensive (customer service cost + shipping cost × 2).
- **Pick-Scan**: Use a handheld scanner to verify the SKU matches the pick list before it leaves the shelf.
- **Pack-Scan**: A second verification step at the packing station before the box is taped. **Requirement**: All products must have unique UPC/EAN barcodes.

## Returns Processing Workflow Integration
Returns should be a mirror of fulfillment, not an afterthought:
1. **Inspection**: Rate the item (A: Resellable, B: Open Box, C: Damaged).
2. **Refurbishing**: Cleaning, re-tagging, and re-polybagging.
3. **Return-to-Shelf**: Scan the item back into a specific Bin Location. The WMS must update the "Available" inventory immediately.

## Best Practices

- **Atomic Fulfillment**: Only mark an order as "Fulfilled" after the carrier label is successfully printed and the manifest is generated.
- **Real-Time Tracking Push**: Push tracking numbers to the customer within 15 minutes of label creation to reduce "Where is my order?" (WISMO) tickets.
- **3PL EDI/SFTP Integration**: If using a 3PL, use automated feeds (EDI 850 for orders, EDI 856 for shipping notices) to ensure data parity.
- **Batch Print Labels**: For high-volume days, print labels in batches of 50 to minimize printer "warm-up" lag and keep packing stations fed.

## Common Pitfalls & Edge Cases

| Problem | Solution |
|---------|----------|
| **Split Shipments** | If an order has items in two different warehouses, the system must support "Partial Fulfillment." Ensure the customer receives two tracking numbers. |
| **Address Validation** | Implement a "Suggest Correction" step during label creation for invalid ZIP codes to prevent "Return to Sender" fees. |
| **Inventory Desync** | If an item is "short-picked" (not on shelf), the picker must flag it immediately to trigger a backorder notification and an inventory cycle count. |
| **Oversized Shipments** | Ensure the workflow prompts the packer to enter dimensions for items over 12" to avoid carrier "Dimensional Weight" surcharges. |

