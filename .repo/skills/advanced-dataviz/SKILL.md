---
name: advanced-dataviz
description: >
  Create interactive data exploration experiences with drill-down, cross-filtering,
  correlation discovery, animated transitions, and responsive layouts. Use this skill
  whenever the user wants to explore, visualize, or interact with data — dashboards,
  charts, data stories, KPI monitors, heatmaps, comparison views, funnel or cohort
  breakdowns. Trigger when the user says "show me the data", "build a dashboard",
  "visualize trends", "find patterns", "compare metrics", or uploads CSV/JSON/Excel
  wanting insight. Also trigger for real-time displays, animated charts, interactive
  filtering, cross-filtering, sparklines, data tables with sorting/search, or any
  multi-view coordinated visualization. NOT for static one-off charts or pure
  statistical computation with no visual output.
---

# Advanced Data Visualization & Interaction

Build interactive data exploration experiences that let users discover insights through
direct manipulation, drill-down, cross-filtering, and animated visual transitions.

## Philosophy

Great data visualization is not decoration — it's a **thinking tool**. Every pixel should
serve cognition: reducing cognitive load, surfacing patterns, and inviting exploration.
The goal is to create artifacts where users forget they're using a tool and start
*having a conversation with the data*.

### Core Principles

1. **Overview first, zoom and filter, details on demand** (Shneiderman's mantra)
2. **Direct manipulation** — click, hover, drag to explore; no modal dialogs
3. **Linked views** — selection in one chart highlights across all views
4. **Progressive disclosure** — don't overwhelm; reveal complexity as users dig deeper
5. **Perceptual honesty** — never distort data; use appropriate encodings
6. **Motion with meaning** — animate transitions to preserve context during state changes

---

## Decision Framework

When the user provides data or requests a visualization, follow this sequence:

### Step 1 — Understand the Data

Before writing any code, characterize the dataset:

| Question | Why It Matters |
|----------|---------------|
| How many rows / columns? | Determines chart type & performance strategy |
| What are the column types? (categorical, numeric, temporal, geographic) | Drives encoding choices |
| What is the grain? (one row = one what?) | Shapes aggregation logic |
| Are there hierarchies? (category → subcategory) | Enables drill-down |
| Are there temporal dimensions? | Enables time-series, animation |
| What questions does the user want answered? | Guides the whole design |

### Step 2 — Choose a Visualization Architecture

Read `references/chart-selection.md` for the full decision tree. Summary:

| User Intent | Recommended Pattern |
|-------------|-------------------|
| Compare values across categories | Bar chart, lollipop, dot plot |
| Show trend over time | Line chart, area chart, sparklines |
| Show part-to-whole | Stacked bar, treemap, sunburst (NOT pie for >5 slices) |
| Reveal distribution | Histogram, box plot, violin, beeswarm |
| Find correlation | Scatter plot, bubble chart, parallel coordinates |
| Show geographic patterns | Choropleth, point map, hex-bin map |
| Explore high-dimensional data | Small multiples, parallel coordinates, radar |
| Monitor KPIs | Card grid with sparklines, gauges, conditional color |
| Discover clusters / outliers | Scatter + brushing, UMAP/t-SNE projection |
| Drill into hierarchies | Treemap, sunburst, expandable table |

### Step 3 — Design the Interaction Model

Read `references/interaction-patterns.md` for full implementation patterns. Key interactions:

- **Hover**: Tooltip with contextual detail (ALWAYS implement)
- **Click**: Drill-down or select/deselect
- **Brush**: Select a range to filter linked views
- **Cross-filter**: Selection in one chart filters all others
- **Search / Filter bar**: Text-based filtering for large datasets
- **Time scrubber**: Animate through temporal data
- **Sort toggle**: Click column headers or axis labels to re-sort
- **Zoom**: Scroll-to-zoom on dense visualizations

### Step 4 — Build with the Right Stack

For React artifacts (`.jsx`), use these available libraries in order of preference:

| Library | Best For | Import |
|---------|----------|--------|
| **Recharts** | Standard charts (bar, line, area, pie, scatter) with React integration | `import { LineChart, ... } from "recharts"` |
| **D3** | Custom/advanced viz, force layouts, geographic, fine control | `import * as d3 from "d3"` |
| **Plotly** | 3D charts, statistical plots, quick prototyping | `import * as Plotly from "plotly"` |
| **Chart.js** | Lightweight canvas-based charts | `import * as Chart from "chart.js"` |
| **Three.js** | 3D data landscapes, immersive viz | `import * as THREE from "three"` |

**Combining libraries is encouraged** — e.g., Recharts for standard charts + D3 for a custom force-directed graph in the same dashboard.

### Step 5 — Apply Visual Design

Read `references/visual-design.md` for the complete design system. Essentials:

- Use a **cohesive, intentional palette** — 1 primary, 1 accent, 3-5 sequential/diverging for data
- Prefer **categorical palettes** that are colorblind-safe (see reference)
- Typography: use a clean sans-serif for data labels; slightly larger for titles
- Whitespace: generous padding between chart panels (min 24px)
- Grid: align charts to a consistent grid for dashboard layouts
- Dark mode: provide toggle; use muted backgrounds (#1a1a2e or similar) with vibrant data colors

---

## Implementation Patterns

### Dashboard Layout (Multi-View)

When building dashboards, use this structure:

```
┌─────────────────────────────────────────────┐
│  HEADER: Title + Date Range + Global Filter │
├──────────┬──────────┬──────────┬────────────┤
│  KPI 1   │  KPI 2   │  KPI 3   │  KPI 4     │  ← Summary cards
├──────────┴──────────┴──────────┴────────────┤
│  PRIMARY CHART (full-width, ~40% height)     │  ← Main insight
├─────────────────────┬───────────────────────┤
│  SECONDARY CHART 1  │  SECONDARY CHART 2    │  ← Supporting views
├─────────────────────┴───────────────────────┤
│  DATA TABLE (sortable, searchable, paginated)│  ← Detail on demand
└─────────────────────────────────────────────┘
```

### Cross-Filtering State Management

Use a shared state pattern to coordinate views:

```jsx
const [filters, setFilters] = useState({
  dateRange: [null, null],
  selectedCategory: null,
  searchTerm: '',
  brushRange: null,
});

// Every chart reads from `filters` and calls `setFilters` on interaction
// Use useMemo to derive filtered data from the full dataset
const filteredData = useMemo(() =>
  rawData.filter(row => applyAllFilters(row, filters)),
  [rawData, filters]
);
```

### Animated Transitions

Wrap state changes in transition logic so users see data "move" rather than "jump":

- Recharts: set `isAnimationActive={true}` with `animationDuration={600}`
- D3: use `.transition().duration(600).ease(d3.easeCubicInOut)`
- CSS: `transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1)` on chart containers

### Responsive Design

All visualizations must work from 375px (mobile) to 1920px+ (desktop):

- Use CSS Grid with `minmax()` and `auto-fit` for dashboard panels
- Recharts `<ResponsiveContainer width="100%" height={300}>` is mandatory
- On mobile: stack charts vertically, collapse filters into a toggleable panel
- Use `matchMedia` or a resize observer to adapt chart density

### Performance for Large Datasets

When data exceeds ~5,000 rows:

- **Virtualize tables** — render only visible rows (implement with simple scroll-based slicing)
- **Aggregate before charting** — don't plot 100K points; bin or downsample
- **Canvas over SVG** — for scatter plots with >2,000 points, use Chart.js or D3 canvas
- **Debounce filters** — 150ms debounce on search/slider inputs
- **useMemo aggressively** — never recompute derived data on every render

### Tooltips (Always Include)

Every data point should have a rich tooltip:

```jsx
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-xl
                    border border-gray-200 p-3 text-sm">
      <p className="font-semibold text-gray-900">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>
          {entry.name}: {formatValue(entry.value)}
        </p>
      ))}
    </div>
  );
};
```

### Data Table with Sort, Search, Pagination

For the "details on demand" layer, always offer a data table:

- Sortable columns (click header to toggle asc/desc)
- Fuzzy search bar at top
- Pagination or virtual scroll for >50 rows
- Click a row to highlight corresponding data point in charts
- Export button (CSV download via Blob URL)

---

## Color Palettes

### Categorical (colorblind-safe)
```js
const CATEGORICAL = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
  '#59a14f', '#edc948', '#b07aa1', '#ff9da7',
  '#9c755f', '#bab0ac'
]; // Tableau 10 — universally readable
```

### Sequential (low → high)
```js
const SEQUENTIAL = ['#f7fbff','#deebf7','#c6dbef','#9ecae1',
  '#6baed6','#4292c6','#2171b5','#084594'];
```

### Diverging (negative ↔ positive)
```js
const DIVERGING = ['#d73027','#f46d43','#fdae61','#fee08b',
  '#d9ef8b','#a6d96a','#66bd63','#1a9850'];
```

---

## Reference Files

Read these for detailed implementation guidance:

| File | When to Read |
|------|-------------|
| `references/chart-selection.md` | Choosing the right chart type for the data and question |
| `references/interaction-patterns.md` | Implementing drill-down, cross-filter, brush, zoom |
| `references/visual-design.md` | Color systems, typography, layout grids, dark mode |

---

## Quality Checklist

Before delivering any visualization artifact, verify:

- [ ] **Every chart has a clear title** explaining what it shows
- [ ] **Axes are labeled** with units (%, $, count, etc.)
- [ ] **Tooltips work** on every data element
- [ ] **At least one interaction** beyond hover (filter, drill-down, sort)
- [ ] **Responsive** — test at 400px and 1200px mentally
- [ ] **Animated transitions** on data changes
- [ ] **Color is accessible** — not relying on red/green alone
- [ ] **Number formatting** — commas for thousands, appropriate decimals
- [ ] **Empty states** — graceful message when filters yield no results
- [ ] **Loading state** — skeleton or spinner while data processes
- [ ] **Export capability** — at minimum, a "Download CSV" button for the filtered data

---

## Anti-Patterns to Avoid

- **Pie charts for >5 categories** — use horizontal bar instead
- **3D charts for 2D data** — never add fake depth; it distorts perception
- **Rainbow color scales** — perceptually non-uniform; use sequential or diverging
- **Truncated Y-axes without warning** — always start at 0 for bar charts
- **Overloaded dashboards** — max 6-8 visual elements per view
- **Tooltips that obscure data** — position intelligently, allow pointer pass-through
- **Animation for animation's sake** — every transition should communicate a data relationship
