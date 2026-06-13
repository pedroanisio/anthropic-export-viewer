# Chart Selection Decision Tree

Use this reference to choose the optimal chart type based on what the user
wants to understand about their data. Start from the user's **intent**, not
from the data shape.

---

## Intent → Chart Type Mapping

### 1. COMPARISON — "How does X compare to Y?"

**Few categories (2-7):**
- Vertical bar chart — default choice for comparing discrete categories
- Grouped bar — comparing 2-3 series across categories
- Lollipop chart — cleaner alternative to bar when many categories share similar values

**Many categories (8-25):**
- Horizontal bar chart — labels are readable; sort by value descending
- Dot plot / Cleveland dot plot — less ink, better for precise reading

**Many categories (25+):**
- Small multiples of sparkline bars — one mini-chart per category
- Searchable/sortable table with inline bar sparklines
- Treemap — for part-to-whole comparison at scale

**Comparing across two dimensions:**
- Heatmap — categories on both axes, color = value
- Bubble chart — size + position encode two variables, color a third

### 2. TREND — "How does this change over time?"

**Single metric:**
- Line chart — default for continuous temporal data
- Area chart — when the filled area communicates volume/magnitude
- Step chart — for data that changes in discrete jumps (pricing, status)

**Multiple metrics (2-4):**
- Multi-line chart — with clear legend and distinct colors
- Stacked area — when showing composition over time
- Small multiples — one line chart per metric, shared X axis

**Multiple metrics (5+):**
- Sparkline grid — compact, one row per metric
- Horizon chart (D3) — extremely compact temporal encoding

**With targets/thresholds:**
- Line chart with reference line (dashed) for target
- Conditional coloring: green above target, red below

**Cyclical time patterns:**
- Radial/polar chart — for hourly/weekly/seasonal cycles
- Calendar heatmap — for daily patterns over months

### 3. DISTRIBUTION — "How is this data spread?"

**Single variable:**
- Histogram — default for showing distribution shape
- Density plot — smoother alternative for continuous data
- Box plot — compact summary (median, quartiles, outliers)

**Compare distributions across groups:**
- Grouped box plot / violin plot — side-by-side comparison
- Ridgeline plot (D3) — stacked density plots, visually striking
- Beeswarm / strip plot — shows individual points when n < 500

**Bivariate distribution:**
- 2D histogram / hexbin — for very large n
- Contour plot — shows density contours

### 4. CORRELATION — "Are X and Y related?"

**Two variables:**
- Scatter plot — the canonical correlation view
- With regression line + confidence band for trend indication
- Add color for a third variable (categorical) or size for a fourth (numeric)

**Many variables (3-8):**
- Scatter plot matrix (SPLOM) — every pair plotted
- Parallel coordinates — each axis is a variable, lines connect values
- Radar/spider chart — up to 8 axes (with caution; hard to read >6)

**Correlation matrix:**
- Heatmap of correlation coefficients — quick overview
- Bubble matrix — size = significance, color = direction

### 5. PART-TO-WHOLE — "What makes up the total?"

**Few parts (2-5):**
- Donut chart — acceptable; show percentage labels
- Stacked bar (100%) — better for comparing across categories

**Many parts (6-20):**
- Treemap — area encodes proportion, supports hierarchy
- Stacked horizontal bar — sorted by size

**Hierarchical:**
- Sunburst — nested rings for multi-level hierarchy
- Icicle chart — rectangular alternative to sunburst
- Expandable treemap with drill-down on click

**Over time:**
- Stacked area chart — shows how composition shifts
- Stream graph — for a more organic, editorial feel

### 6. FLOW & RELATIONSHIP — "How do things connect?"

- Sankey diagram (D3) — flow between stages, width = volume
- Chord diagram — relationships between entities in a circle
- Network / force-directed graph (D3) — entities as nodes, connections as edges
- Arc diagram — simpler alternative to force layout for small networks

### 7. GEOGRAPHIC — "Where does this happen?"

- Choropleth — color-coded regions (countries, states, zip codes)
- Proportional symbol map — circles on a map, size = value
- Hex-bin map — aggregated geographic density
- Dot density map — one dot per unit (population, stores, etc.)

Note: For geographic visualization in React artifacts, use D3's geo projection
capabilities with GeoJSON/TopoJSON data, or SVG-based simplified maps.

### 8. RANKING — "What's the order?"

- Horizontal bar chart (sorted) — the gold standard
- Bump chart — rank changes over time
- Slope chart — compare rank between two time points

---

## Data Size Considerations

| Rows | Strategy |
|------|----------|
| < 100 | Any chart type; show individual points freely |
| 100 - 1,000 | Standard charts; scatter plots fine |
| 1,000 - 10,000 | Aggregate for bar/line; use canvas for scatter |
| 10,000 - 100,000 | Pre-aggregate; hex-bin for scatter; virtualize tables |
| 100,000+ | Server-side aggregation needed; show summaries only |

---

## Composition Rules

When building multi-chart dashboards, combine chart types that answer
complementary questions:

| Primary Chart | Good Companion | Why |
|--------------|----------------|-----|
| Line (trend) | Bar (composition breakdown) | See both the trend and what drives it |
| Scatter (correlation) | Histograms on margins | See distribution of each variable |
| Bar (comparison) | Data table | Let users see exact values |
| Map (geographic) | Bar (top-N by region) | Compare regions precisely |
| Treemap (hierarchy) | Line (trend of selected node) | Drill into a segment's trend |

---

## Chart Type Red Flags

Avoid these combinations:

- **Pie chart + many slices** → Use bar chart instead
- **Dual Y-axis line chart** → Use small multiples (dual axes mislead correlation)
- **Stacked bar with many series** → Simplify to top-N + "other"
- **3D anything** → Almost always worse than 2D equivalent
- **Gauge/speedometer** → Use a simple number + sparkline instead
- **Word cloud** → Use a sorted bar chart of word frequencies
