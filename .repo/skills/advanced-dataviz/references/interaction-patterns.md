# Interaction Patterns for Data Visualization

This reference covers implementation patterns for every major interaction type.
All examples use React + Recharts/D3, the primary stack for artifacts.

---

## 1. DRILL-DOWN

**What it is:** Click on a summary element to reveal more detailed data beneath it.

**When to use:** Hierarchical data (region → city → store), time aggregation
(year → quarter → month → day), category breakdowns.

**Pattern:**

```jsx
const [drillPath, setDrillPath] = useState([]); // e.g., ['US', 'California']

const currentData = useMemo(() => {
  let data = rawData;
  for (const key of drillPath) {
    data = data.filter(d => d[drillLevels[drillPath.indexOf(key)]] === key);
  }
  // Aggregate to next level
  return aggregateBy(data, drillLevels[drillPath.length]);
}, [rawData, drillPath]);

const handleDrillDown = (clickedValue) => {
  if (drillPath.length < drillLevels.length - 1) {
    setDrillPath([...drillPath, clickedValue]);
  }
};

const handleDrillUp = () => {
  setDrillPath(drillPath.slice(0, -1));
};
```

**UX requirements:**
- Show a breadcrumb trail: `All > US > California > Los Angeles`
- Animate the transition (bars shrink/grow into new bars)
- Provide a "Back" or "↑ Up" button AND clickable breadcrumbs
- Change the chart title to reflect current drill level
- Show a subtle "click to drill down" hint on first interaction

---

## 2. CROSS-FILTERING (Linked Views)

**What it is:** Selecting data in one chart filters or highlights data in all other charts.

**When to use:** Any multi-chart dashboard. This is the single most powerful
interaction for data discovery — implement it by default.

**Pattern:**

```jsx
// Central filter state
const [activeFilters, setActiveFilters] = useState({
  selectedCategory: null,  // from bar chart click
  brushedRange: null,      // from time series brush
  searchTerm: '',          // from search input
  selectedPoints: new Set(), // from scatter lasso
});

// Derive filtered data once
const filteredData = useMemo(() => {
  return rawData.filter(row => {
    if (activeFilters.selectedCategory &&
        row.category !== activeFilters.selectedCategory) return false;
    if (activeFilters.brushedRange) {
      const [min, max] = activeFilters.brushedRange;
      if (row.date < min || row.date > max) return false;
    }
    if (activeFilters.searchTerm &&
        !row.name.toLowerCase().includes(activeFilters.searchTerm.toLowerCase()))
      return false;
    return true;
  });
}, [rawData, activeFilters]);

// Each chart receives filteredData and a setter for its own filter dimension
<BarChart data={filteredData}
  onClick={(d) => setActiveFilters(f => ({
    ...f, selectedCategory: f.selectedCategory === d.category ? null : d.category
  }))} />

<LineChart data={filteredData}
  onBrush={(range) => setActiveFilters(f => ({ ...f, brushedRange: range }))} />
```

**UX requirements:**
- Highlight selected items, dim (don't hide) unselected items (opacity 0.15-0.3)
- Show an active filter badge/pill: `Category: Electronics ✕`
- Click again to deselect (toggle behavior)
- "Clear all filters" button always visible when any filter is active
- Count indicator: "Showing 234 of 1,205 records"

---

## 3. BRUSHING & RANGE SELECTION

**What it is:** Click and drag to select a range on an axis.

**Recharts implementation:**
```jsx
<LineChart>
  <Brush
    dataKey="date"
    height={40}
    stroke="#4e79a7"
    onChange={({ startIndex, endIndex }) => {
      const range = [data[startIndex].date, data[endIndex].date];
      setActiveFilters(f => ({ ...f, brushedRange: range }));
    }}
  />
</LineChart>
```

**D3 implementation:**
```jsx
const brush = d3.brushX()
  .extent([[0, 0], [width, height]])
  .on('end', (event) => {
    if (!event.selection) { clearBrush(); return; }
    const [x0, x1] = event.selection.map(xScale.invert);
    setActiveFilters(f => ({ ...f, brushedRange: [x0, x1] }));
  });

svg.append('g').call(brush);
```

**UX requirements:**
- Visual handle on both ends of the brush
- Shaded region indicating selected range
- Snap to data points when close
- Double-click to reset brush
- Show selected range as text: "Jan 2024 — Mar 2024"

---

## 4. HOVER TOOLTIPS (Rich)

**What it is:** Display contextual information when hovering over data elements.

**Pattern for Recharts:**
```jsx
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(255,255,255,0.97)',
      backdropFilter: 'blur(8px)',
      borderRadius: 8,
      padding: '12px 16px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
      border: '1px solid rgba(0,0,0,0.08)',
      maxWidth: 280,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{
          display: 'flex', justifyContent: 'space-between', gap: 16,
          color: entry.color, marginBottom: 2,
        }}>
          <span>{entry.name}</span>
          <span style={{ fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
            {formatValue(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};
```

**UX requirements:**
- Appear within 50ms (no delay)
- Position to avoid chart edges (flip when near boundary)
- Include a subtle color swatch matching the data series
- Format numbers with locale-appropriate separators
- For scatter plots, show both X and Y values plus any encoded dimensions
- Never obscure the data point being hovered

---

## 5. SORTING & REORDERING

**What it is:** Click column headers or axis labels to re-sort data.

**Pattern:**
```jsx
const [sortConfig, setSortConfig] = useState({ key: 'value', dir: 'desc' });

const sortedData = useMemo(() => {
  return [...filteredData].sort((a, b) => {
    const mult = sortConfig.dir === 'asc' ? 1 : -1;
    return mult * (a[sortConfig.key] > b[sortConfig.key] ? 1 : -1);
  });
}, [filteredData, sortConfig]);

const toggleSort = (key) => {
  setSortConfig(prev => ({
    key,
    dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc',
  }));
};
```

**UX requirements:**
- Arrow indicator on sorted column (▲ / ▼)
- Animate bar chart reordering with CSS `transition: transform 0.4s`
- Default to descending (people usually want to see the biggest first)

---

## 6. SEARCH & TEXT FILTERING

**What it is:** Type to filter data across all visible text fields.

**Pattern:**
```jsx
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounced(searchTerm, 150);

// Simple debounce hook
function useDebounced(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
```

**UX requirements:**
- Search icon in the input field
- Clear button (✕) when text is present
- Highlight matching text in results
- Show result count: "3 matches"
- No results state: "No items match your search"

---

## 7. TIME ANIMATION (Play Through)

**What it is:** Animate through temporal data to see evolution over time.

**Pattern:**
```jsx
const [timeIndex, setTimeIndex] = useState(0);
const [isPlaying, setIsPlaying] = useState(false);

useEffect(() => {
  if (!isPlaying) return;
  const interval = setInterval(() => {
    setTimeIndex(prev => {
      if (prev >= timeSteps.length - 1) { setIsPlaying(false); return prev; }
      return prev + 1;
    });
  }, 800); // ms per frame
  return () => clearInterval(interval);
}, [isPlaying, timeSteps.length]);

// Render
<div className="flex items-center gap-3">
  <button onClick={() => setIsPlaying(!isPlaying)}>
    {isPlaying ? '⏸' : '▶'}
  </button>
  <input type="range" min={0} max={timeSteps.length - 1}
    value={timeIndex}
    onChange={(e) => setTimeIndex(Number(e.target.value))} />
  <span>{timeSteps[timeIndex]}</span>
</div>
```

**UX requirements:**
- Play/Pause button
- Scrubber slider for manual control
- Current time label prominently displayed
- Speed control (0.5x, 1x, 2x)
- Loop toggle option

---

## 8. DATA TABLE (Detail Layer)

**What it is:** Sortable, searchable, paginated table showing raw or aggregated data.

**Core features:**
- Column header click to sort (with direction indicator)
- Search bar filtering across all columns
- Pagination: show 20 rows per page with prev/next controls
- Row click to highlight in connected charts
- Conditional formatting: color cells by value ranges
- Sticky header on scroll
- Column resize by dragging headers (optional, advanced)

**Export pattern:**
```jsx
const exportCSV = () => {
  const headers = columns.map(c => c.label).join(',');
  const rows = filteredData.map(row =>
    columns.map(c => JSON.stringify(row[c.key] ?? '')).join(',')
  );
  const csv = [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'data-export.csv'; a.click();
  URL.revokeObjectURL(url);
};
```

---

## 9. ZOOM & PAN

**When to use:** Dense scatter plots, time series with long history, geographic maps.

**D3 zoom pattern:**
```jsx
const zoom = d3.zoom()
  .scaleExtent([1, 20])
  .on('zoom', (event) => {
    chartGroup.attr('transform', event.transform);
  });

svg.call(zoom);

// Reset button
const resetZoom = () => svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
```

**UX requirements:**
- Scroll wheel to zoom, drag to pan
- "Reset zoom" button always visible during zoom
- Mini-map indicator showing viewport position (for very large canvases)
- Limit zoom extent to prevent losing data from view

---

## 10. ANNOTATION & INSIGHT CALLOUTS

**What it is:** Highlight specific data points with contextual annotations.

**Pattern:**
```jsx
const annotations = [
  { date: '2024-03-15', label: 'Product Launch', y: 45000 },
  { date: '2024-07-01', label: 'Market Correction', y: 32000 },
];

// Render as Recharts ReferenceLine + custom label
{annotations.map(a => (
  <ReferenceLine key={a.date} x={a.date} stroke="#e15759"
    strokeDasharray="4 4"
    label={{ value: a.label, position: 'top', fill: '#e15759' }} />
))}
```

**UX requirements:**
- Subtle dashed line or marker
- Label positioned to avoid overlap
- Optional expand-on-hover for longer annotation text
- Support user-added annotations if building an exploratory tool
