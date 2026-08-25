# Data Source Badges Reference

All badges used in the final report to indicate data provenance.

## Badge Styles

### Option 1: Cite Badge (Recommended) — Semantic citation with clickable links

| Badge | HTML | Preview |
|-------|------|----------|
| Jungle Scout | `<cite>[Jungle Scout](https://www.junglescout.com)</cite>` | <cite>[Jungle Scout](https://www.junglescout.com)</cite> |
| Web | `<cite>[Web](https://www.google.com)</cite>` | <cite>[Web](https://www.google.com)</cite> |
| Amazon | `<cite>[Amazon](https://www.amazon.com)</cite>` | <cite>[Amazon](https://www.amazon.com)</cite> |
| TikTok&nbsp;Shop | `<cite>[TikTok Shop](https://shop.tiktok.com)</cite>` | <cite>[TikTok Shop](https://shop.tiktok.com)</cite> |
| Temu | `<cite>[Temu](https://www.temu.com)</cite>` | <cite>[Temu](https://www.temu.com)</cite> |
| Shein | `<cite>[Shein](https://www.shein.com)</cite>` | <cite>[Shein](https://www.shein.com)</cite> |
| Shopee | `<cite>[Shopee](https://www.shopee.com)</cite>` | <cite>[Shopee](https://www.shopee.com)</cite> |
| Company&nbsp;Survey | `<cite>[Company Survey](#)</cite>` | <cite>[Company Survey](#)</cite> |
| Google&nbsp;Trends | `<cite>[Google Trends](https://trends.google.com)</cite>` | <cite>[Google Trends](https://trends.google.com)</cite> |
| Alibaba | `<cite>[Alibaba](https://www.alibaba.com)</cite>` | <cite>[Alibaba](https://www.alibaba.com)</cite> |
| Web&nbsp;Search | `<cite>[Web Search](https://www.google.com/search)</cite>` | <cite>[Web Search](https://www.google.com/search)</cite> |
| Tariff&nbsp;Search | `<cite>[Tariff Search](https://hts.usitc.gov)</cite>` | <cite>[Tariff Search](https://hts.usitc.gov)</cite> |
| matplotlib | `<cite>[matplotlib](https://matplotlib.org)</cite>` | <cite>[matplotlib](https://matplotlib.org)</cite> |

> 💡 **Cite Tag Advantage**: Using `<cite>` tags provides semantic citation markup with clickable links to data sources.

---

## Color Reference

| Platform | Brand Color | Hex | Notes |
|----------|------------|-----|-------|
| Jungle Scout | Blue | `#1592E6` | Official brand color |
| Web | Green | `#2ea44f` | Standard success green |
| Amazon | Orange | `#FF9900` | Brand orange |
| TikTok | Pink | `#FE2C55` | TikTok brand pink |
| Temu | Orange | `#FF6A00` | Brand orange |
| Shein | Purple | `#9B59B6` | Brand purple |
| Shopee | Orange-Red | `#EE4D2D` | Brand orange-red |
| Company Survey | Purple | `#8B5CF6` | Purple |
| Google | Multi-Color | `#4285F4` `#34A853` `#FBBC05` `#EA4335` | Google multi-color (blue, green, yellow, red) |
| Alibaba | Orange | `#FF6A00` | Brand orange |
| Web Search | Amber | `#F59E0B` | Amber |
| Tariff Search | Sky Blue | `#0EA5E9` | Sky blue |
| matplotlib | Gray | `#6B7280` | Gray |

---

## Badge Placement Rules

1. **Section headers**: Each section MUST have relevant source badge(s) next to the `##` header
2. **Sub-question blocks**: Place source badge ONCE on the `**Data Acquisition`** line only
3. **Multiple sources in one sub-question**: Place each distinct badge once — primary on `Data Acquisition`, additional on the specific line where that different source is first introduced
4. **Product tables**: Tag with the specific platform badge on the table header line
5. **General rule**: Within any continuous block from the SAME source, use the badge only ONCE at the beginning

---

## Usage Examples

### Cite Badge (Recommended)

```html
<cite>[Jungle Scout](https://www.junglescout.com)</cite> data
```

### Multiple badges inline

```html
<cite>[Amazon](https://www.amazon.com)</cite>
<cite>[Web](https://www.google.com)</cite>
```

### In section header

```html
## Product Analysis <cite>[Amazon](https://www.amazon.com)</cite>
```

---

## Preview Gallery

### E-commerce Platforms
<cite>[Amazon](https://www.amazon.com)</cite>
<cite>[TikTok Shop](https://shop.tiktok.com)</cite>
<cite>[Temu](https://www.temu.com)</cite>
<cite>[Shein](https://www.shein.com)</cite>
<cite>[Shopee](https://www.shopee.com)</cite>
<cite>[Alibaba](https://www.alibaba.com)</cite>

### Data & Research
<cite>[Jungle Scout](https://www.junglescout.com)</cite>
<cite>[Google Trends](https://trends.google.com)</cite>
<cite>[Company Survey](#)</cite>

### Utilities
<cite>[Web](https://www.google.com)</cite>
<cite>[Web Search](https://www.google.com/search)</cite>
<cite>[Tariff Search](https://hts.usitc.gov)</cite>
<cite>[matplotlib](https://matplotlib.org)</cite>

