---
name: "iande::adv-dataviz"
description: >
  Create interactive data exploration experiences with drill-down, cross-filtering,
  correlation discovery, animated transitions, and responsive layouts. Use this skill
  whenever the user wants to explore, visualize, or interact with data — dashboards,
  charts, data stories, KPI monitors, heatmaps, comparison views, funnel or cohort
  breakdowns. Trigger when the user says "show me the data", "build a dashboard",
  "visualize trends", "find patterns", "compare metrics", or uploads CSV/JSON/Excel
  wanting insight. Also trigger for real-time displays, animated charts, interactive
  filtering, cross-filtering, sparklines, data tables with sorting/search, or any
  multi-view coordinated visualization. Trigger for AI-powered data analysis where
  the artifact calls the Anthropic API to interpret patterns or generate narratives.
  NOT for static one-off charts or pure statistical computation with no visual output.
---

# Advanced Data Visualization & Interaction

Build interactive data exploration experiences. Every artifact produced by this skill
must be **typed, testable, and beautiful** — in that order.

## Core Contract

| Priority | Requirement |
|----------|------------|
| 1 — Code quality | TypeScript types on every prop, state, and derived value. No `any`. |
| 2 — Output quality | Professional visual polish — not "default Recharts with blue bars." |
| 3 — Decision logic | Choose the right chart for the data *before* writing code. |
| 4 — Interaction depth | Every view is explorable: hover, filter, drill, export minimum. |

---

## Architecture: TypeScript-First

All artifacts are `.jsx` files but must use TypeScript-style documentation and
runtime guards. Since the artifact environment doesn't support `.tsx`, enforce
types via JSDoc and runtime validation.

### Typing Strategy

```jsx
/**
 * @typedef {{
 *   date: string;
 *   category: string;
 *   value: number;
 *   metadata?: Record<string, unknown>;
 * }} DataRow
 *
 * @typedef {{
 *   dateRange: [Date | null, Date | null];
 *   selectedCategory: string | null;
 *   searchTerm: string;
 *   brushRange: [number, number] | null;
 * }} FilterState
 *
 * @typedef {'asc' | 'desc'} SortDirection
 * @typedef {{ key: string; dir: SortDirection }} SortConfig
 */
```

### Runtime Validation

Always validate data at the boundary (file upload, pasted JSON, generated data):

```jsx
/** @param {unknown[]} raw @returns {DataRow[]} */
function validateRows(raw) {
  return raw.filter(r =>
    r != null &&
    typeof r === 'object' &&
    typeof r.date === 'string' &&
    typeof r.value === 'number' &&
    !Number.isNaN(r.value)
  );
}
```

### State Management Pattern

Use a single reducer for complex dashboards — **not** a pile of `useState` calls.
This eliminates stale-closure bugs and makes state transitions auditable:

```jsx
/** @typedef {FilterState & { sortConfig: SortConfig; drillPath: string[] }} DashState */

function dashReducer(state, action) {
  switch (action.type) {
    case 'SET_CATEGORY':
      return { ...state, selectedCategory:
        state.selectedCategory === action.payload ? null : action.payload };
    case 'SET_BRUSH':
      return { ...state, brushRange: action.payload };
    case 'SET_SEARCH':
      return { ...state, searchTerm: action.payload };
    case 'DRILL_DOWN':
      return { ...state, drillPath: [...state.drillPath, action.payload] };
    case 'DRILL_UP':
      return { ...state, drillPath: state.drillPath.slice(0, -1) };
    case 'RESET':
      return INITIAL_STATE;
    default:
      return state;
  }
}
```

---

## Data Inference Engine

Before choosing a chart, **characterize the data programmatically**. Do not guess.

```jsx
/** @param {Record<string, unknown>[]} rows */
function inferSchema(rows) {
  if (!rows.length) return { columns: [], rowCount: 0 };
  const sample = rows.slice(0, 100);
  const columns = Object.keys(sample[0]).map(key => {
    const values = sample.map(r => r[key]).filter(v => v != null);
    const types = new Set(values.map(v => typeof v));
    const isDate = values.every(v =>
      typeof v === 'string' && !Number.isNaN(Date.parse(v))
    );
    const unique = new Set(values);
    return {
      key,
      type: isDate ? 'temporal'
        : types.has('number') ? 'numeric'
        : unique.size <= 20 ? 'categorical'
        : 'text',
      cardinality: unique.size,
      hasNulls: sample.some(r => r[key] == null),
      sample: [...unique].slice(0, 5),
    };
  });
  return { columns, rowCount: rows.length };
}
```

Use the inferred schema to auto-select chart type — see `references/chart-selection.md`.

---

## Decision Framework

### Step 1 — Infer Schema (above)

### Step 2 — Match Intent to Chart

Read `references/chart-selection.md` for the full decision tree. The key rule:
**start from what the user wants to know, not from what the data looks like.**

| User intent | Primary chart | Companion |
|------------|--------------|-----------|
| Compare values | Horizontal bar (sorted) | Data table |
| Trend over time | Line + area fill | Sparkline KPIs |
| Part-to-whole | Treemap or stacked bar | Donut (≤5 slices only) |
| Distribution | Histogram or violin | Box-plot summary |
| Correlation | Scatter + regression | Marginal histograms |
| Flow / relationship | Sankey (D3) or chord | Force-directed graph |
| Geographic | Choropleth or dot map | Top-N bar by region |
| Ranking | Bump chart | Slope chart |

### Step 3 — Design the Layout

Read `references/interaction-patterns.md` for implementation details.

```
┌───────────────────────────────────────────────┐
│  HEADER: Title · Date Range · Global Filters  │
├─────────┬─────────┬─────────┬────────────────┤
│  KPI 1  │  KPI 2  │  KPI 3  │  KPI 4         │  ← summary cards
├─────────┴─────────┴─────────┴────────────────┤
│  PRIMARY CHART (full-width, ~40% height)      │  ← main insight
├──────────────────────┬───────────────────────┤
│  SECONDARY CHART 1   │  SECONDARY CHART 2    │  ← supporting
├──────────────────────┴───────────────────────┤
│  DATA TABLE (sort, search, paginate, export)  │  ← detail on demand
└───────────────────────────────────────────────┘
```

### Step 4 — Apply Visual Design

Read `references/visual-design.md`. Key mandates:

- **No default Recharts colors.** Always supply an explicit palette.
- **Font: DM Sans** loaded from Google Fonts. Tabular-nums on all numbers.
- **Dark mode toggle** on every dashboard via CSS variables.
- **Panel styling**: `border-radius: 12px`, subtle shadow, 1px border.
- **Entrance animation**: staggered fade-slide-in on panels.
- **`prefers-reduced-motion`**: always respect.

---

## Advanced D3 Patterns

For charts Recharts cannot handle, use D3 directly inside a `useRef` + `useEffect`
pattern. **Never mix D3 DOM mutations with React's virtual DOM on the same elements.**

### Pattern: D3 in React (safe)

```jsx
function D3Chart({ data, width, height }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !data.length) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // clear previous render

    // ... D3 rendering logic here ...

    return () => { svg.selectAll('*').remove(); }; // cleanup
  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
}
```

### Available Advanced Charts (D3)

| Chart | When | Reference |
|-------|------|-----------|
| Force-directed graph | Network/relationship data, entity connections | `references/interaction-patterns.md` §Force |
| Sankey diagram | Flow between stages, conversion funnels | `references/interaction-patterns.md` §Sankey |
| Choropleth / geo | Geographic distribution | `references/chart-selection.md` §Geographic |
| Sunburst | Hierarchical part-to-whole with drill-down | `references/chart-selection.md` §Hierarchy |
| Parallel coordinates | High-dimensional comparison (5+ variables) | `references/chart-selection.md` §Correlation |
| Calendar heatmap | Daily patterns over months/years | `references/chart-selection.md` §Temporal |

---

## AI-Powered Analysis

Artifacts can call the Anthropic API to generate narrative insights from data.
Use this for "explain this data", "what patterns do you see", or "generate a summary".

### Pattern: Insight Generator

```jsx
async function analyzeData(data, question) {
  const sample = data.slice(0, 200); // keep token count sane
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages: [{
        role: 'user',
        content: `Analyze this dataset and answer: "${question}"

Data (first ${sample.length} of ${data.length} rows):
${JSON.stringify(sample, null, 2)}

Respond ONLY with a JSON object — no markdown, no backticks:
{
  "summary": "2-3 sentence plain-language summary",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "anomalies": ["anomaly 1"] or [],
  "suggestedCharts": ["chart type 1", "chart type 2"]
}`
      }],
    }),
  });
  const result = await response.json();
  const text = result.content?.find(b => b.type === 'text')?.text || '';
  return JSON.parse(text.replace(/```json|```/g, '').trim());
}
```

### UX for AI Analysis

- Show a sparkle icon button labeled **"Analyze"** or **"Ask AI"**
- Display a loading skeleton with a pulsing animation while waiting
- Render insights in a collapsible panel above the charts
- Each insight is clickable — clicking applies the relevant filter or highlights relevant data
- Always show a disclaimer: *"AI-generated analysis — verify against your data."*

---

## Performance Rules

| Data size | Strategy |
|-----------|----------|
| < 1K rows | Render everything. SVG is fine. |
| 1K – 5K | `useMemo` on all derived data. Debounce filters (150ms). |
| 5K – 20K | Canvas rendering for scatter. Virtualize tables. Aggregate before charting. |
| 20K+ | Pre-aggregate into bins/buckets. Never iterate full dataset per render. Web Workers if > 16ms computation. |

### Virtualized Table (no library)

```jsx
function VirtualTable({ rows, rowHeight = 36, visibleCount = 20 }) {
  const [scrollTop, setScrollTop] = useState(0);
  const startIdx = Math.floor(scrollTop / rowHeight);
  const visible = rows.slice(startIdx, startIdx + visibleCount + 1);
  const totalHeight = rows.length * rowHeight;

  return (
    <div style={{ height: visibleCount * rowHeight, overflow: 'auto' }}
         onScroll={e => setScrollTop(e.currentTarget.scrollTop)}>
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visible.map((row, i) => (
          <div key={startIdx + i}
               style={{ position: 'absolute', top: (startIdx + i) * rowHeight,
                        height: rowHeight, width: '100%' }}>
            {/* render row cells */}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Debounce Hook

```jsx
function useDebounced(value, delay = 150) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
```

---

## Interaction Robustness

The #1 source of broken interactions is **event handler references changing on
every render**, causing stale closures or lost bindings.

### Rules

1. **Wrap handlers in `useCallback`** with correct dependency arrays.
2. **Never define handlers inline in JSX** — extract and memoize.
3. **Recharts `onClick`**: callback signature is `(data, index, event)` for bar/line/pie.
   Always destructure correctly. Verify clicking actually works.
4. **D3 event listeners**: attach in `useEffect`, clean up in the return function.
5. **Cross-filter dispatch**: always use the reducer pattern, never nested `setState` calls.
6. **Tooltip positioning**: always compute relative to the chart container, not the viewport.

### Tooltip Positioning (D3)

```jsx
const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, data: null });

// In D3 mouseover handler:
const rect = svgRef.current.getBoundingClientRect();
setTooltip({
  show: true,
  x: event.clientX - rect.left,
  y: event.clientY - rect.top,
  data: d,
});
```

---

## Visual Quality Checklist

Before delivering any artifact, verify every item:

- [ ] **Explicit color palette** — no library defaults
- [ ] **DM Sans loaded** — or clean system-ui fallback
- [ ] **Tabular-nums** on all numeric displays
- [ ] **Chart titles** — every panel has a clear, descriptive title
- [ ] **Axis labels with units** — `Revenue ($K)`, `Time (months)`, etc.
- [ ] **Tooltips on every data element**
- [ ] **At least one interaction** beyond hover (filter, drill, sort)
- [ ] **Responsive** — works at 400px and 1400px
- [ ] **Animated transitions** on filter/drill/sort changes
- [ ] **Empty state** — graceful message when filters yield zero results
- [ ] **Loading state** — skeleton shimmer while data processes
- [ ] **Export** — CSV download button for filtered data
- [ ] **Dark mode toggle** — CSS variable switching
- [ ] **Reduced motion** — `prefers-reduced-motion` media query honored
- [ ] **No `any` types** — every value typed via JSDoc
- [ ] **No stale closures** — handlers wrapped in `useCallback`

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Pie chart > 5 slices | Horizontal bar, sorted |
| 3D charts | 2D equivalent (always) |
| Dual Y-axis | Small multiples (dual axes mislead) |
| Rainbow color scale | Sequential or diverging palette |
| Default Recharts blue | Explicit Tableau 10 or custom palette |
| `useState` × 8 for filters | `useReducer` with typed actions |
| Inline handlers in JSX | `useCallback` + extracted functions |
| `any` or untyped props | JSDoc `@typedef` on every shape |
| Truncated Y-axis (bar) | Start at 0; note if intentionally truncated |
| > 8 panels per dashboard | Prioritize; use tabs or progressive reveal |

---

## Reference Files

| File | Read When |
|------|-----------|
| `references/chart-selection.md` | Choosing the right chart for the data and question |
| `references/interaction-patterns.md` | Implementing drill-down, cross-filter, brush, zoom, Sankey, force layout |
| `references/visual-design.md` | Color systems, typography, layout grids, dark mode, animation |
