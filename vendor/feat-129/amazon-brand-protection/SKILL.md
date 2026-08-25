---
name: amazon-brand-protection
description: >-
  Protect Amazon brands from listing hijackers, counterfeiters, and policy violations. 
  Use this skill when users report hijackers on their listing, counterfeit products, or need to enroll in Amazon Brand Registry. 
  It also covers intellectual property protection, responding to false IP complaints or suspensions, 
  and using tools like Transparency, Project Zero, and IP Alert.
---

# Amazon Brand Protection

## The Brand Protection Stack

Amazon provides a layered set of protection tools. Use them in combination:


| Tool                         | Access Requirement          | What It Does                                                        |
| ---------------------------- | --------------------------- | ------------------------------------------------------------------- |
| **Brand Registry**           | Registered trademark        | Foundation tool; unlocks all other protections                      |
| **IP Alert**                 | Brand Registry              | Alerts you when suspected infringers appear on your listings        |
| **Transparency**             | Brand Registry              | Serializes units with unique codes; counterfeit units can't be sold |
| **Project Zero**             | Brand Registry + invitation | AI-powered proactive counterfeit removal; self-service removal      |
| **Report a Violation (RAV)** | Brand Registry              | Submit IP infringement claims directly                              |
| **A+ Content & Brand Story** | Brand Registry              | Differentiates your listing; harder for hijackers to replicate      |


---

## Amazon Brand Registry Setup

**Requirements:**

- Active registered trademark in the selling country (USPTO for US, EUIPO for EU, etc.)
- Trademark must show your brand name as it appears on products and packaging
- Pending trademark applications may qualify for IP Accelerator program

**Enrollment steps:**

1. Go to brandservices.amazon.com
2. Enroll with trademark registration number + issuing authority
3. Amazon verifies with trademark office (typically 2-5 business days)
4. Once approved: access to Brand Registry dashboard in Seller Central

**Important:** Trademark registration takes 8-12 months in the US.
Apply early — you cannot get Brand Registry without it.

---

## Listing Hijacker Detection & Response

**What is a hijacker?**
An unauthorized seller who adds themselves as an offer on your branded listing,
often selling counterfeit or grey-market goods at lower prices.

**Detection signals:**

- Buy Box lost to an unknown seller
- Sudden appearance of new sellers on your listing
- Customer complaints about product quality or different packaging
- Reviews mentioning "not the same as described"

**How to check:** Seller Central → Inventory → Manage Inventory → click the number in "Offers" column

**Response protocol (in order):**

**Step 1: Test buy** (most effective first step)
Purchase one unit from the hijacker's offer.
When it arrives, if it's counterfeit or different: you have physical evidence for Amazon's enforcement team.

**Step 2: Cease and desist message**
Send a professional message via Buyer-Seller Messaging: "You are selling on a listing owned by [Brand]. This is a trademark violation. Remove your offer within 48 hours or we will file an IP complaint with Amazon and pursue legal action."
(Many hijackers remove themselves after receiving this.)

**Step 3: Report a Violation (RAV)**
Brand Registry → Report a Violation → Submit the ASIN + hijacker's seller ID + evidence
Amazon typically acts within 3-5 business days.

**Step 4: Transparency enrollment** (preventive)
Apply units with unique QR codes. Amazon's systems and customers can verify authenticity.
Counterfeit units without valid Transparency codes cannot be sold on your listing.

---

## Protecting Against False IP Complaints

Your listing can be taken down if a competitor files a false IP complaint against you.

**Prevention:**

- Register your trademark before scaling
- Keep records of all product photography, packaging, and design files with timestamps
- Document your brand development history (design files, launch dates, marketing materials)
- Never use stock photos that might be owned by a third party

**Response to a false complaint:**

1. Identify the complainant from Amazon's complaint notice
2. Send a counter-notice via Seller Central → Performance → Account Health → Intellectual Property Complaints
3. Provide evidence that you own the rights or have license to use the content
4. If the complaint is clearly false (DMCA abuse), you can sue the complainant in US federal court

---

## Brand Registry Features for Listing Control

Once enrolled, Brand Registry gives you:

**Listing authority:**

- Your brand's content takes precedence over 3P seller edits
- Only you can update title, images, and description on your branded listing
- Suppresses unauthorized content changes by other sellers

**Search and Report:**

- Search for infringing listings by image, keyword, or ASIN
- Bulk reporting tool for high-volume IP violations
- Automated protections that remove clear infringement without human review

**Brand Analytics:**

- Search Query Performance: See which search terms lead to your product page
- Market Basket Analysis: What products customers buy alongside yours
- Repeat Purchase Behavior: Percentage of customers who buy again within 1 year
- Demographics report: Age, income, gender, marital status of your buyers

---

## Project Zero (Advanced Protection)

Project Zero is an invitation-only program that gives brands:

- Self-service counterfeit removal (remove listings instantly, no waiting for Amazon review)
- Machine learning model trained on your brand to proactively scan and remove counterfeits
- Transparency code integration for authenticated units only

**How to get invited:**

- Must have Brand Registry
- Strong track record of accurate IP complaints (low error rate)
- Apply via the Project Zero waitlist in Brand Registry

---

## Key IP Terms Every Amazon Seller Should Know


| Term                 | Definition                                                               |
| -------------------- | ------------------------------------------------------------------------ |
| **Trademark**        | Protects brand name, logo, slogan                                        |
| **Copyright**        | Protects creative works (photos, product descriptions, packaging design) |
| **Patent (Utility)** | Protects how a product works or is manufactured                          |
| **Patent (Design)**  | Protects how a product looks                                             |
| **Trade Dress**      | Protects distinctive product appearance (color, shape, packaging)        |
| **ASIN Gating**      | Restricting who can sell on your listing (requires approval)             |


---

## Brand Protection KPIs


| KPI                                               | Check Frequency | Action Trigger                                           |
| ------------------------------------------------- | --------------- | -------------------------------------------------------- |
| Number of sellers on main ASINs                   | Daily           | >1 unauthorized seller → initiate hijacker protocol      |
| Buy Box win rate                                  | Weekly          | <90% → investigate if hijacker has Buy Box               |
| Negative reviews mentioning "fake" or "different" | Weekly          | Any → test buy from all active offers                    |
| IP complaint notices received                     | Immediately     | Respond within 7 days to avoid permanent listing removal |
| Transparency scan failure rate                    | Monthly         | >0.5% → investigate supply chain                         |

