# Visual Design System

Every visualization must look intentionally designed, not "default library output."
Apply these standards consistently across all artifacts.

---

## Color System

### Categorical Palettes (distinct groups)

**Tableau 10 (default — colorblind-safe, high contrast):**
```jsx
const TABLEAU_10 = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
  '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac'
];
```

**Vibrant (dark backgrounds):**
```jsx
const VIBRANT = [
  '#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236',
  '#166a8f', '#00a950', '#58595b', '#8549ba', '#ff6384'
];
```

**Muted (light backgrounds, sophisticated feel):**
```jsx
const MUTED = [
  '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
  '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd'
];
```

### Sequential Palettes (low → high)

```jsx
const SEQ_BLUE  = ['#f7fbff','#deebf7','#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#084594'];
const SEQ_GREEN = ['#f7fcf5','#e5f5e0','#c7e9c0','#a1d99b','#74c476','#41ab5d','#238b45','#005a32'];
const SEQ_WARM  = ['#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#b10026'];
```

### Diverging Palettes (negative ↔ positive)

```jsx
const DIV_RD_BU = ['#b2182b','#d6604d','#f4a582','#fddbc7','#d1e5f0','#92c5de','#4393c3','#2166ac'];
const DIV_BR_TL = ['#8c510a','#bf812d','#dfc27d','#f6e8c3','#c7eae5','#80cdc1','#35978f','#01665e'];
```

### Color Rules

1. **Max 10 categorical colors** — group smaller into "Other"
2. **Never red/green only** — always pair with shape, texture, or label
3. **Sequential for ordered data only** — never categories
4. **Opacity 0.15–0.3 for de-emphasis** — preserves color identity
5. **Highlight**: saturated version of the palette primary
6. **Background**: `#ffffff` light, `#0f172a` dark

### Palette Utility

```jsx
/** @param {number} index @param {string[]} palette @returns {string} */
function getColor(index, palette = TABLEAU_10) {
  return palette[index % palette.length];
}

/** @param {string} hex @param {number} opacity @returns {string} */
function withOpacity(hex, opacity) {
  const alpha = Math.round(opacity * 255).toString(16).padStart(2, '0');
  return hex + alpha;
}
```

---

## Typography

### Font Loading

Always load DM Sans from Google Fonts. Include in the artifact's HTML/JSX:

```jsx
// In React artifacts, add to the component:
const fontLink = document.createElement('link');
fontLink.href = 'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap';
fontLink.rel = 'stylesheet';
document.head.appendChild(fontLink);
```

### Font Stack

```css
--font-data: 'DM Sans', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;
```

### Sizing

| Element | Size | Weight |
|---------|------|--------|
| Dashboard title | 24–28px | 700 |
| Chart title | 16–18px | 600 |
| Axis label | 11–12px | 500 |
| Tick label | 10–11px | 400 |
| Tooltip header | 13px | 600 |
| Tooltip value | 12px | 400 |
| KPI big number | 32–48px | 700 |
| KPI label | 12–13px | 500 |

### Number Formatting

```jsx
/** @type {Record<string, (v: number) => string>} */
const fmt = {
  number:   (v) => v.toLocaleString('en-US'),
  currency: (v) => '$' + v.toLocaleString('en-US', { minimumFractionDigits: 0 }),
  percent:  (v) => (v * 100).toFixed(1) + '%',
  compact:  (v) => {
    if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + 'B';
    if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1) + 'M';
    if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + 'K';
    return v.toString();
  },
  date: (v) => new Date(v).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  }),
};

// CRITICAL: all numeric elements must use tabular-nums
// Apply via: style={{ fontVariantNumeric: 'tabular-nums' }}
```

---

## Layout System

### Dashboard Grid

```css
.dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  padding: 24px;
  max-width: 1440px;
  margin: 0 auto;
  font-family: 'DM Sans', system-ui, sans-serif;
}

.chart-panel {
  background: var(--panel-bg);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid var(--border-color);
}

.chart-panel.full-width { grid-column: 1 / -1; }
```

### KPI Cards

```css
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  grid-column: 1 / -1;
}

.kpi-card {
  padding: 16px 20px;
  border-radius: 10px;
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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

.kpi-change { font-size: 13px; margin-top: 6px; }
.kpi-change.positive { color: #22c55e; }
.kpi-change.negative { color: #ef4444; }
```

### Responsive Breakpoints

```css
@media (max-width: 640px) {
  .dashboard { grid-template-columns: 1fr; padding: 12px; }
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .chart-panel { padding: 14px; }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .dashboard { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1025px) {
  .dashboard { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
}
```

---

## Dark Mode

Every dashboard must have a theme toggle. Use CSS variables:

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

### Theme Toggle Implementation

```jsx
function useTheme() {
  const [theme, setTheme] = useState('light');
  const toggle = useCallback(() => {
    setTheme(prev => {
      const next = prev === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      return next;
    });
  }, []);
  return { theme, toggle };
}
```

### Chart-Specific Adjustments

- Grid lines: `var(--grid-line)` at 0.3 opacity
- Axis labels: `var(--text-secondary)`
- Tooltip: `var(--panel-bg)` + `backdrop-filter: blur(12px)`
- Data colors: increase saturation slightly on dark backgrounds

---

## Animation

### Entrance (page load)

```css
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

- Recharts: `isAnimationActive={true}`, `animationDuration={600}`
- D3: `.transition().duration(600).ease(d3.easeCubicInOut)`
- CSS bars: `transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1)`

### Loading Skeleton

```jsx
function Skeleton({ width = '100%', height = 16 }) {
  return (
    <div style={{
      width, height, borderRadius: 6,
      background: 'linear-gradient(90deg, var(--hover-bg) 25%, var(--border-color) 50%, var(--hover-bg) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
    }} />
  );
}
// Add to CSS: @keyframes shimmer { to { background-position: -200% 0; } }
```

### Performance Rules

- Animate `transform` and `opacity` only (GPU-accelerated)
- `will-change: transform` on frequently animated elements
- **Always** honor reduced motion:

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

Use Lucide React (available in artifacts):

```jsx
import {
  TrendingUp, TrendingDown,   // KPI change
  Filter, Search, Download,    // controls
  RefreshCw, ChevronDown, X,   // UI
  Sun, Moon,                   // theme toggle
  Sparkles,                    // AI analysis button
} from "lucide-react";
```

---

## Accessibility Checklist

- [ ] Color contrast ≥ 4.5:1 text, ≥ 3:1 graphical
- [ ] Pattern/texture as secondary encoding (not color alone)
- [ ] Charts have `aria-label` or `role="img"` + `aria-label`
- [ ] Tab navigation on interactive elements
- [ ] Tooltips appear on keyboard focus, not just hover
- [ ] Screen reader announcements for data changes
- [ ] `prefers-reduced-motion` respected
- [ ] Focus ring visible on all interactive elements
