# Chart Design Guide

Professional chart generation guidelines for Amazon market data visualization.

## Tool Selection

### Seaborn vs Matplotlib

**Use Seaborn for**:
- Statistical plots (distributions, correlations)
- Multi-variable comparisons
- Categorical data visualization
- When you want built-in themes

**Use Matplotlib for**:
- Custom layouts and annotations
- Pie charts, radar charts
- Fine-grained control
- Complex multi-subplot layouts

## Common Chart Types for Market Analysis

### 1. Sales Trend (Time Series)

```python
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Prepare data
dates = [datetime.strptime(d["date"][:10], "%Y-%m-%d") for d in daily_data]
sales = [d["estimated_units_sold"] for d in daily_data]

# Create plot
plt.figure(figsize=(12, 6))
plt.plot(dates, sales, linewidth=2, color='#2E86AB')
plt.fill_between(dates, sales, alpha=0.3, color='#2E86AB')

plt.title('Sales Trend (90 Days)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Units Sold', fontsize=12)
plt.grid(True, alpha=0.3, linestyle='--')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('sales_trend.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 2. Price Distribution (Histogram)

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Extract prices
prices = [p["attributes"]["price"] for p in products if p["attributes"].get("price")]

# Create plot
plt.figure(figsize=(10, 6))
sns.histplot(prices, bins=20, kde=True, color='#A23B72')

plt.title('Price Distribution', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Price ($)', fontsize=12)
plt.ylabel('Number of Products', fontsize=12)
plt.axvline(sum(prices)/len(prices), color='red', linestyle='--', 
            label=f'Average: ${sum(prices)/len(prices):.2f}')
plt.legend()
plt.tight_layout()
plt.savefig('price_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 3. Market Share (Pie Chart)

```python
import matplotlib.pyplot as plt

# Prepare data
brands = [b["brand"] for b in sov_data["attributes"]["brands"][:8]]
shares = [b["combined_weighted_sov"] * 100 for b in sov_data["attributes"]["brands"][:8]]

# Add "Others" category
others = 100 - sum(shares)
if others > 0:
    brands.append("Others")
    shares.append(others)

# Create plot
plt.figure(figsize=(10, 8))
colors = plt.cm.Set3(range(len(brands)))
plt.pie(shares, labels=brands, autopct='%1.1f%%', startangle=90, colors=colors)
plt.title('Market Share by Brand', fontsize=16, fontweight='bold', pad=20)
plt.axis('equal')
plt.tight_layout()
plt.savefig('market_share.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 4. Opportunity Matrix (Scatter Plot)

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Prepare data
search_volumes = [kw["attributes"]["monthly_search_volume_exact"] for kw in keywords]
competitions = [kw["attributes"]["organic_product_count"] for kw in keywords]
names = [kw["attributes"]["name"] for kw in keywords]

# Create plot
plt.figure(figsize=(12, 8))
plt.scatter(competitions, search_volumes, s=100, alpha=0.6, c='#F18F01')

# Annotate top opportunities
for i in range(min(10, len(names))):
    plt.annotate(names[i], (competitions[i], search_volumes[i]), 
                fontsize=8, alpha=0.7)

plt.title('Keyword Opportunity Matrix', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Competition (Organic Products)', fontsize=12)
plt.ylabel('Search Volume (Monthly)', fontsize=12)
plt.grid(True, alpha=0.3, linestyle='--')

# Add quadrant lines
plt.axhline(y=5000, color='red', linestyle='--', alpha=0.5, label='High Volume Threshold')
plt.axvline(x=300, color='blue', linestyle='--', alpha=0.5, label='Low Competition Threshold')
plt.legend()

plt.tight_layout()
plt.savefig('opportunity_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 5. Multi-Metric Comparison (Horizontal Bar)

```python
import matplotlib.pyplot as plt
import numpy as np

# Prepare data
products_names = [p["attributes"]["title"][:30] for p in top_products[:10]]
scores = [calculate_opportunity_score(p)["total_score"] for p in top_products[:10]]

# Create plot
plt.figure(figsize=(12, 8))
y_pos = np.arange(len(products_names))
colors = ['#06A77D' if s >= 4.0 else '#F18F01' if s >= 3.0 else '#D62828' for s in scores]

plt.barh(y_pos, scores, color=colors, alpha=0.8)
plt.yticks(y_pos, products_names, fontsize=10)
plt.xlabel('Opportunity Score', fontsize=12)
plt.title('Top 10 Products by Opportunity Score', fontsize=16, fontweight='bold', pad=20)
plt.axvline(x=4.0, color='green', linestyle='--', alpha=0.5, label='High Opportunity')
plt.axvline(x=3.0, color='orange', linestyle='--', alpha=0.5, label='Moderate')
plt.legend()
plt.tight_layout()
plt.savefig('product_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 6. Radar Chart (Multi-Attribute)

```python
import matplotlib.pyplot as plt
import numpy as np

# Prepare data
categories = ['Demand', 'Competition', 'Profitability', 'Quality', 'Position']
product1_scores = [4.5, 3.8, 4.2, 4.0, 3.5]
product2_scores = [3.2, 4.5, 3.0, 4.5, 4.0]

# Number of variables
N = len(categories)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

# Close the plot
product1_scores += product1_scores[:1]
product2_scores += product2_scores[:1]

# Create plot
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

ax.plot(angles, product1_scores, 'o-', linewidth=2, label='Product A', color='#2E86AB')
ax.fill(angles, product1_scores, alpha=0.25, color='#2E86AB')

ax.plot(angles, product2_scores, 'o-', linewidth=2, label='Product B', color='#A23B72')
ax.fill(angles, product2_scores, alpha=0.25, color='#A23B72')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)
ax.set_ylim(0, 5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=10)
ax.grid(True)

plt.title('Product Comparison (Multi-Attribute)', fontsize=16, fontweight='bold', pad=20)
plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig('radar_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
```

### 7. Heatmap (Correlation Matrix)

```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Prepare data
data = {
    'Price': [p["attributes"]["price"] for p in products],
    'Sales': [p["attributes"]["approximate_30_day_units_sold"] for p in products],
    'Reviews': [p["attributes"]["reviews"] for p in products],
    'Rating': [p["attributes"]["rating"] for p in products],
    'BSR': [p["attributes"]["product_rank"] for p in products]
}
df = pd.DataFrame(data)

# Calculate correlation
corr = df.corr()

# Create plot
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})

plt.title('Metric Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Styling Best Practices

### Color Palette

```python
# Professional color scheme
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'success': '#06A77D',      # Green
    'warning': '#F18F01',      # Orange
    'danger': '#D62828',       # Red
    'neutral': '#6C757D'       # Gray
}
```

### Font Settings

```python
import matplotlib.pyplot as plt

# Set global font
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['font.size'] = 10

# Title: 16pt, bold
# Axis labels: 12pt
# Tick labels: 10pt
# Annotations: 8-9pt
```

### Figure Size Guidelines

```python
# Single chart: (10, 6) or (12, 6)
# Comparison charts: (12, 8)
# Radar/Pie: (10, 10) for square aspect
# Multi-subplot: (14, 10) or larger
```

## Anti-Patterns to Avoid

❌ **Don't**:
- Use 3D charts (hard to read)
- Overload with too many data points
- Use rainbow color schemes
- Forget axis labels
- Use default figure sizes (too small)
- Save as low DPI (< 150)

✅ **Do**:
- Use consistent color scheme
- Add grid for readability
- Include legends when comparing
- Save as PNG with DPI=300
- Use `tight_layout()` to prevent clipping
- Add meaningful titles

## Seaborn v0.12+ API Updates

**Old (Deprecated)**:
```python
sns.distplot(data)  # Deprecated
```

**New (Recommended)**:
```python
sns.histplot(data, kde=True)  # Use histplot with kde=True
```

**Old**:
```python
sns.boxplot(x='category', y='value', data=df, palette='Set2')
```

**New** (same, but be explicit):
```python
sns.boxplot(data=df, x='category', y='value', palette='Set2')
```

## Complete Example: Market Analysis Dashboard

```python
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Create figure with subplots
fig = plt.figure(figsize=(16, 12))
gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

# 1. Sales Trend
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(dates, sales, linewidth=2, color='#2E86AB')
ax1.fill_between(dates, sales, alpha=0.3, color='#2E86AB')
ax1.set_title('Sales Trend (90 Days)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel('Units Sold')
ax1.grid(True, alpha=0.3)

# 2. Price Distribution
ax2 = fig.add_subplot(gs[1, 0])
sns.histplot(prices, bins=20, kde=True, color='#A23B72', ax=ax2)
ax2.set_title('Price Distribution', fontsize=14, fontweight='bold')
ax2.set_xlabel('Price ($)')

# 3. Market Share
ax3 = fig.add_subplot(gs[1, 1])
ax3.pie(shares, labels=brands, autopct='%1.1f%%', startangle=90)
ax3.set_title('Market Share', fontsize=14, fontweight='bold')

# 4. Opportunity Matrix
ax4 = fig.add_subplot(gs[2, :])
ax4.scatter(competitions, search_volumes, s=100, alpha=0.6, c='#F18F01')
ax4.set_title('Keyword Opportunity Matrix', fontsize=14, fontweight='bold')
ax4.set_xlabel('Competition')
ax4.set_ylabel('Search Volume')
ax4.grid(True, alpha=0.3)

plt.suptitle('Market Analysis Dashboard', fontsize=18, fontweight='bold', y=0.995)
plt.savefig('dashboard.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Tips for Jungle Scout Data

1. **Sales Data**: Use line charts with area fill for trends
2. **Price Data**: Use histograms with KDE for distribution
3. **Market Share**: Use pie charts (limit to top 8-10 brands)
4. **Keywords**: Use scatter plots for opportunity matrix
5. **Product Comparison**: Use horizontal bar charts or radar charts
6. **Correlations**: Use heatmaps for metric relationships

## Performance Tips

- Close figures after saving: `plt.close()`
- Use `tight_layout()` before saving
- Save as PNG (not PDF) for web display
- Use DPI=300 for print quality, DPI=150 for web
- Limit data points in scatter plots (< 1000)

