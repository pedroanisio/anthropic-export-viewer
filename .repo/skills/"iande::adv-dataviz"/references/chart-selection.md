# Chart Selection Decision Tree

Choose the optimal chart based on the user's **intent**, not the data shape.
When intent is ambiguous, use the schema-driven auto-selector below.

---

## Schema-Driven Auto-Selection

When the user says "visualize this" without specifying intent, use the inferred
schema (from `inferSchema()` in SKILL.md) to pick automatically:

```jsx
/**
 * @param {{ columns: Array<{ key: string; type: string; cardinality: number }>;
 *           rowCount: number }} schema
 * @returns {{ primary: string; secondary: string; reason: string }}
 */
function autoSelectChart(schema) {
  const { columns, rowCount } = schema;
  const temporal = columns.filter(c => c.type === 'temporal');
  const numeric = columns.filter(c => c.type === 'numeric');
  const categorical = columns.filter(c => c.type === 'categorical');

  // Time series: temporal + numeric → line chart
  if (temporal.length >= 1 && numeric.length >= 1) {
    return {
      primary: numeric.length <= 3 ? 'line' : 'sparkline-grid',
      secondary: 'data-table',
      reason: `${temporal.length} temporal + ${numeric.length} numeric → trend`,
    };
  }

  // Categorical + numeric → bar comparison
  if (categorical.length >= 1 && numeric.length >= 1) {
    const cat = categorical[0];
    return {
      primary: cat.cardinality <= 7 ? 'vertical-bar'
        : cat.cardinality <= 25 ? 'horizontal-bar'
        : 'treemap',
      secondary: 'data-table',
      reason: `categorical (${cat.cardinality} values) + numeric → comparison`,
    };
  }

  // Multiple numeric, no categorical → correlation
  if (numeric.length >= 2 && categorical.length === 0) {
    return {
      primary: numeric.length === 2 ? 'scatter' : 'parallel-coordinates',
      secondary: 'correlation-heatmap',
      reason: `${numeric.length} numeric columns → correlation exploration`,
    };
  }

  // Single numeric → distribution
  if (numeric.length === 1 && categorical.length === 0) {
    return {
      primary: 'histogram',
      secondary: 'box-plot',
      reason: 'single numeric → distribution',
    };
  }

  // Fallback
  return {
    primary: 'data-table',
    secondary: 'none',
    reason: 'ambiguous schema — default to table view',
  };
}
```

---

## Intent → Chart Type Mapping

### 1. COMPARISON — "How does X compare to Y?"

**Few categories (2–7):**
- Vertical bar — default comparison
- Grouped bar — 2–3 series across categories
- Lollipop — cleaner when categories share similar values

**Many categories (8–25):**
- Horizontal bar — labels readable; sort descending
- Dot plot / Cleveland dot plot — less ink, better precision

**Many categories (25+):**
- Small multiples of sparkline bars
- Searchable/sortable table with inline sparklines
- Treemap for part-to-whole at scale

**Two-dimensional comparison:**
- Heatmap — categories on both axes, color = value
- Bubble chart — size + position + color encode 3 variables

### 2. TREND — "How does this change over time?"

**Single metric:**
- Line chart — default for continuous temporal data
- Area chart — when filled area communicates volume
- Step chart — discrete jumps (pricing, status changes)

**Multiple metrics (2–4):**
- Multi-line — distinct colors, clear legend
- Stacked area — composition over time
- Small multiples — one line per metric, shared X axis

**Multiple metrics (5+):**
- Sparkline grid — compact, one row per metric
- Horizon chart (D3) — extremely compact temporal encoding

**Cyclical patterns:**
- Radial/polar chart — hourly/weekly/seasonal
- Calendar heatmap — daily patterns over months

### 3. DISTRIBUTION — "How is this data spread?"

**Single variable:**
- Histogram — default
- Density plot — smoother, continuous data
- Box plot — compact summary (median, quartiles, outliers)

**Compare across groups:**
- Grouped box / violin — side-by-side
- Ridgeline (D3) — stacked density, visually striking
- Beeswarm / strip — individual points when n < 500

**Bivariate:**
- 2D histogram / hexbin — very large n
- Contour plot — density contours

### 4. CORRELATION — "Are X and Y related?"

**Two variables:**
- Scatter plot — canonical correlation view
- With regression line + confidence band
- Color = third variable (categorical), size = fourth (numeric)

**Many variables (3–8):**
- Scatter plot matrix (SPLOM)
- Parallel coordinates — each axis a variable, lines connect values
- Radar/spider — up to 8 axes (with caution; >6 hard to read)

**Correlation matrix:**
- Heatmap of coefficients — quick overview
- Bubble matrix — size = significance, color = direction

### 5. PART-TO-WHOLE — "What makes up the total?"

**Few parts (2–5):**
- Donut chart — acceptable; show percentages
- Stacked bar (100%) — better for comparing across categories

**Many parts (6–20):**
- Treemap — area encodes proportion, supports hierarchy
- Stacked horizontal bar — sorted by size

**Hierarchical:**
- Sunburst — nested rings for multi-level hierarchy
- Icicle chart — rectangular alternative
- Expandable treemap with click-to-drill

**Over time:**
- Stacked area — composition shifts
- Stream graph — more organic, editorial feel

### 6. FLOW & RELATIONSHIP — "How do things connect?"

- Sankey (D3) — flow between stages, width = volume
- Chord diagram — circular relationships between entities
- Force-directed graph (D3) — nodes + edges, interactive
- Arc diagram — simpler alternative for small networks

### 7. GEOGRAPHIC — "Where does this happen?"

- Choropleth — color-coded regions
- Proportional symbol map — circles on map, size = value
- Hex-bin map — aggregated density
- Dot density — one dot per unit

In React artifacts, use D3 geo projections with GeoJSON/TopoJSON.
For a quick US/world map, inline simplified SVG paths.

### 8. RANKING — "What's the order?"

- Horizontal bar (sorted) — gold standard
- Bump chart — rank changes over time
- Slope chart — compare rank between two points

---

## Data Size Scaling

| Rows | Strategy |
|------|----------|
| < 100 | Anything; show individual points |
| 100 – 1K | Standard charts; scatter fine |
| 1K – 10K | Aggregate for bar/line; canvas scatter |
| 10K – 100K | Pre-aggregate; hex-bin scatter; virtualize tables |
| 100K+ | Server-side aggregation; show summaries only |

---

## Chart Composition Rules

| Primary Chart | Good Companion | Why |
|--------------|----------------|-----|
| Line (trend) | Bar (composition) | Trend + what drives it |
| Scatter (correlation) | Marginal histograms | Distribution of each variable |
| Bar (comparison) | Data table | Exact values on demand |
| Map (geographic) | Top-N bar by region | Precise region comparison |
| Treemap (hierarchy) | Line (trend of selected) | Drill into segment's trend |
| Sankey (flow) | Bar (volume by stage) | Total + flow detail |

---

## Chart Type Red Flags

| Avoid | Use Instead |
|-------|------------|
| Pie + many slices | Horizontal bar |
| Dual Y-axis | Small multiples |
| Stacked bar + many series | Top-N + "Other" |
| 3D anything | 2D equivalent |
| Gauge / speedometer | Number + sparkline |
| Word cloud | Sorted bar of frequencies |
