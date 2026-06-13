# Visual Design System for Data Visualization

A comprehensive design system that makes data beautiful, readable, and accessible.
Apply these standards consistently across all visualization artifacts.

---

## Color System

### Categorical Palettes (use for distinct groups)

**Tableau 10 (default — colorblind-safe, high contrast):**
```js
const TABLEAU_10 = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
  '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac'
];
```

**Vibrant (for dark backgrounds):**
```js
const VIBRANT = [
  '#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236',
  '#166a8f', '#00a950', '#58595b', '#8549ba', '#ff6384'
];
```

**Muted (for light backgrounds with a sophisticated feel):**
```js
const MUTED = [
  '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
  '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd'
];
```

### Sequential Palettes (use for low-to-high values)

**Blue single-hue:**
```js
const SEQ_BLUE = ['#f7fbff','#deebf7','#c6dbef','#9ecae1',
  '#6baed6','#4292c6','#2171b5','#084594'];
```

**Green single-hue:**
```js
const SEQ_GREEN = ['#f7fcf5','#e5f5e0','#c7e9c0','#a1d99b',
  '#74c476','#41ab5d','#238b45','#005a32'];
```

**Warm (yellow → red):**
```js
const SEQ_WARM = ['#ffffcc','#ffeda0','#fed976','#feb24c',
  '#fd8d3c','#fc4e2a','#e31a1c','#b10026'];
```

### Diverging Palettes (use for values with a meaningful midpoint)

**Red ↔ Blue (default):**
```js
const DIV_RD_BU = ['#b2182b','#d6604d','#f4a582','#fddbc7',
  '#d1e5f0','#92c5de','#4393c3','#2166ac'];
```

**Brown ↔ Teal:**
```js
const DIV_BR_TL = ['#8c510a','#bf812d','#dfc27d','#f6e8c3',
  '#c7eae5','#80cdc1','#35978f','#01665e'];
```

### Color Rules

1. **Maximum 10 categorical colors** — group smaller categories into "Other"
2. **Never use red/green as the only differentiator** — colorblind users can't distinguish
3. **Sequential palettes for ordered data ONLY** — never for categories
4. **Use opacity (0.15-0.3) for de-emphasis**, not gray — preserves color identity
5. **Highlight color**: use a saturated version of the primary palette color
6. **Background**: pure white (#ffffff) for light mode, deep blue-black (#0f172a) for dark

---

## Typography

### Font Stack
```css
/* Data labels, axes, tooltips */
--font-data: 'DM Sans', 'IBM Plex Sans', system-ui, sans-serif;
/* Titles and headers */
--font-display: 'DM Sans', 'Space Grotesk', system-ui, sans-serif;
/* Monospace numbers in tables */
--font-mono: 'IBM Plex Mono', 'JetBrains Mono', monospace;
```

Load from Google Fonts if in HTML:
```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Font Sizes
| Element | Size | Weight |
|---------|------|--------|
| Dashboard title | 24-28px | 700 |
| Chart title | 16-18px | 600 |
| Axis label | 11-12px | 500 |
| Tick label | 10-11px | 400 |
| Tooltip header | 13px | 600 |
| Tooltip value | 12px | 400 |
| KPI big number | 32-48px | 700 |
| KPI label | 12-13px | 500 |

### Number Formatting
```js
const fmt = {
  number: (v) => v.toLocaleString('en-US'),
  currency: (v) => '$' + v.toLocaleString('en-US', { minimumFractionDigits: 0 }),
  percent: (v) => (v * 100).toFixed(1) + '%',
  compact: (v) => {
    if (v >= 1e9) return (v/1e9).toFixed(1) + 'B';
    if (v >= 1e6) return (v/1e6).toFixed(1) + 'M';
    if (v >= 1e3) return (v/1e3).toFixed(1) + 'K';
    return v.toString();
  },
  date: (v) => new Date(v).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  }),
};
```

---

## Layout System

### Dashboard Grid
Use CSS Grid with consistent spacing:
```css
.dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
}

.chart-panel {
  background: var(--panel-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid var(--border-color);
}

.chart-panel.full-width {
  grid-column: 1 / -1;
}

.chart-panel.half-width {
  grid-column: span 1;
}
```

### KPI Cards
```css
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  grid-column: 1 / -1; /* always full width */
}

.kpi-card {
  padding: 16px 20px;
  border-radius: 10px;
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.kpi-label {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.kpi-change {
  font-size: 13px;
  margin-top: 6px;
}
.kpi-change.positive { color: #22c55e; }
.kpi-change.negative { color: #ef4444; }
```

### Responsive Breakpoints
```css
/* Mobile: stack everything vertically */
@media (max-width: 640px) {
  .dashboard { grid-template-columns: 1fr; padding: 12px; }
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .chart-panel { padding: 14px; }
}

/* Tablet: 2-column */
@media (min-width: 641px) and (max-width: 1024px) {
  .dashboard { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop: auto-fit with minimum */
@media (min-width: 1025px) {
  .dashboard { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
}
```

---

## Dark Mode

Provide a theme toggle. Use CSS variables for easy switching:

```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --panel-bg: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --hover-bg: #f1f5f9;
  --grid-line: #e2e8f0;
}

[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --panel-bg: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border-color: #334155;
  --hover-bg: #334155;
  --grid-line: #334155;
}
```

### Chart-Specific Dark Mode Adjustments
- Grid lines: use `var(--grid-line)` with 0.3 opacity
- Axis labels: use `var(--text-secondary)`
- Tooltip: use `var(--panel-bg)` with `backdrop-filter: blur(12px)`
- Data colors: increase saturation slightly on dark backgrounds

---

## Animation Guidelines

### Entrance Animations (page load / data change)
```css
/* Stagger chart panels on load */
.chart-panel {
  opacity: 0;
  transform: translateY(12px);
  animation: fadeSlideIn 0.5s ease-out forwards;
}

.chart-panel:nth-child(1) { animation-delay: 0.05s; }
.chart-panel:nth-child(2) { animation-delay: 0.1s; }
.chart-panel:nth-child(3) { animation-delay: 0.15s; }
.chart-panel:nth-child(4) { animation-delay: 0.2s; }

@keyframes fadeSlideIn {
  to { opacity: 1; transform: translateY(0); }
}
```

### Data Transitions
```css
/* Smooth bar height changes */
.recharts-bar-rectangle { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }

/* Smooth line chart morphing */
.recharts-line-curve { transition: d 0.5s ease-in-out; }
```

### Micro-Interactions
```css
/* Hover lift on cards */
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: all 0.2s ease;
}

/* Active filter pill */
.filter-pill {
  transition: all 0.15s ease;
}
.filter-pill:hover {
  background: var(--hover-bg);
}
```

### Performance Rules
- Animate `transform` and `opacity` only (GPU-accelerated)
- Use `will-change: transform` on frequently animated elements
- Disable animations for `prefers-reduced-motion: reduce`

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Iconography

Use Lucide React icons (available in artifacts):
```jsx
import { TrendingUp, TrendingDown, Filter, Search,
         Download, RefreshCw, ChevronDown, X } from "lucide-react";
```

Common data viz icons:
- `TrendingUp` / `TrendingDown` — KPI change indicators
- `Filter` — filter panel toggle
- `Search` — search input
- `Download` — CSV export
- `RefreshCw` — refresh data
- `ChevronDown` — dropdown menus
- `X` — clear filter / close

---

## Accessibility Checklist

- [ ] Color contrast ratio ≥ 4.5:1 for text, ≥ 3:1 for graphical elements
- [ ] Patterns or textures as secondary encoding (not color alone)
- [ ] All charts have descriptive `aria-label` or `role="img"` with `aria-label`
- [ ] Tab navigation works for interactive elements
- [ ] Tooltips appear on keyboard focus, not just hover
- [ ] Screen reader announcements for data changes
- [ ] Reduced motion support via media query
