---
name: aliexpress-supplier-evaluator
description: >-
  Evaluate B2C suppliers on global platforms like AliExpress or Temu for reliability, shipping costs, and product authenticity.
---

## When to Use
Trigger this skill when a user is sourcing products from overseas B2C platforms (e.g., AliExpress, DHgate, Temu) for personal use, resale, or dropshipping. Use it to audit vendor reliability, calculate true landed costs, and avoid common procurement scams.

## Core Vendor Evaluation Framework
Do not rely on star ratings alone. Evaluate vendors using this weighted scorecard:

| Metric | Red Flag (High Risk) | Neutral (Needs Testing) | Green Flag (Preferred) |
| :--- | :--- | :--- | :--- |
| **Store Longevity** | < 6 months | 6 months - 2 years | > 3 years |
| **Follower Count** | < 500 | 500 - 5,000 | > 10,000 |
| **Response Speed** | > 24 hours | 12 - 24 hours | < 12 hours |
| **Positive Feedback** | < 94% | 94% - 97% | > 98% |
| **Feedback Quality** | Only 5-star with no text | Generic "Good" text | Detailed photos/videos from buyers |

### Decision Criteria for "Trustworthy" Status
- **Strict Mode**: Requires Green Flags in all 5 categories. Recommended for high-value items (>$100).
- **Standard Mode**: Requires at least 3 Green Flags and no Red Flags.
- **Risk Mode**: Proceed only with a small test sample if any Red Flags are present.

## Landed Cost Calculation
The listed price on B2C platforms is rarely the final cost. Always compute:
`Total Landed Cost = (Item Price * Quantity) + Shipping + Payment Fees + Import Duties/VAT`

### Key Variables:
- **Shipping Tiers**: 
  - Budget (40-60 days): High risk of loss, no tracking.
  - Standard (15-25 days): Best balance, usually includes tracking (e.g., AliExpress Standard Shipping).
  - Premium (3-7 days): Expensive, but necessary for time-sensitive inventory.
- **Import Taxes**: Thresholds vary by country (e.g., EU VAT rules, US De Minimis $800).
- **Payment Fees**: Most platforms charge 2-3% for credit card or currency conversion.

## Sourcing Multi-Vendor Comparison
Before purchasing, perform a "Cross-Vendor Audit":
1. **Reverse Image Search**: Identify if 10+ vendors are using the same factory photos. If so, price is your primary lever, but check store response rates.
2. **Review Discrepancy**: If Vendor A is 50% cheaper than Vendor B but has no photo reviews, Vendor A likely uses inferior materials or is a bait-and-switch.
3. **Sample Comparison**: For long-term sourcing, buy 1 unit from 3 top-rated vendors to compare actual build quality and packaging.

## Dispute & Protection Management
- **The "Unboxing" Rule**: Always record a continuous video of opening the package. This is the only indisputable evidence for "empty box" or "damaged on arrival" claims.
- **Dispute Timing**: 
  - Open "Item Not Received" 5 days after the Estimated Delivery Date.
  - Open "Quality Dispute" within 10 days of delivery confirmation.
  - **Negotiation Tip**: If the seller asks you to close the dispute to "process a refund," REFUSE. Closing a dispute often voids your platform protection.

## Scam Detection & Edge Cases
- **Fake Tracking**: If the tracking number shows "Delivered" to a different city/zip code, immediately file for "Wrong Address" fraud.
- **Extortion**: If a seller asks for extra shipping fees *after* payment, cancel the order and report the store.
- **Counterfeit Risk**: If a brand-name item is discounted >60% off MSRP, assume it is a replica. Counterfeits may be seized by customs, leading to total loss.

