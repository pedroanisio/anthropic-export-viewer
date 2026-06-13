# Interaction Patterns for Data Visualization

Implementation patterns for every major interaction type. All examples use
JSDoc-typed React + Recharts/D3.

## Table of Contents

1. [Drill-Down](#1-drill-down)
2. [Cross-Filtering](#2-cross-filtering)
3. [Brushing & Range Selection](#3-brushing--range-selection)
4. [Hover Tooltips](#4-hover-tooltips)
5. [Sorting & Reordering](#5-sorting--reordering)
6. [Search & Text Filtering](#6-search--text-filtering)
7. [Time Animation](#7-time-animation)
8. [Data Table](#8-data-table)
9. [Zoom & Pan](#9-zoom--pan)
10. [Annotations](#10-annotations)
11. [Sankey Diagram (D3)](#11-sankey)
12. [Force-Directed Graph (D3)](#12-force)

---

## 1. DRILL-DOWN

Click a summary element to reveal more detailed data beneath it.

**When:** Hierarchical data (region → city → store), time aggregation
(year → quarter → month), category breakdowns.

```jsx
/**
 * @typedef {string[]} DrillPath
 * @typedef {{ levels: string[]; labels: Record<string, string> }} DrillConfig
 */

const DRILL_CONFIG = {
  levels: ['region', 'state', 'city'],
  labels: { region: 'Region', state: 'State', city: 'City' },
};

function useDrill(config) {
  const [path, setPath] = useState([]);

  const drillDown = useCallback((value) => {
    setPath(prev =>
      prev.length < config.levels.length - 1
        ? [...prev, value]
        : prev
    );
  }, [config.levels.length]);

  const drillUp = useCallback((toIndex = -1) => {
    setPath(prev =>
      toIndex < 0 ? prev.slice(0, -1) : prev.slice(0, toIndex)
    );
  }, []);

  const currentLevel = config.levels[path.length];
  const canDrillDown = path.length < config.levels.length - 1;

  return { path, drillDown, drillUp, currentLevel, canDrillDown };
}
```

**UX requirements:**
- Breadcrumb trail: `All > US > California > Los Angeles`
- Animated transition (bars shrink/grow into new bars)
- "Back" button AND clickable breadcrumbs (click "US" to jump there)
- Chart title updates to reflect current drill level
- Cursor hint: `cursor: pointer` when `canDrillDown` is true

---

## 2. CROSS-FILTERING

Selection in one chart filters or highlights data in all other charts.
**Implement by default on every multi-chart dashboard.**

```jsx
/**
 * @typedef {{
 *   selectedCategory: string | null;
 *   brushedRange: [number, number] | null;
 *   searchTerm: string;
 *   selectedPoints: Set<string>;
 * }} FilterState
 */

const INITIAL_FILTERS = {
  selectedCategory: null,
  brushedRange: null,
  searchTerm: '',
  selectedPoints: new Set(),
};

function filterReducer(state, action) {
  switch (action.type) {
    case 'TOGGLE_CATEGORY':
      return { ...state, selectedCategory:
        state.selectedCategory === action.payload ? null : action.payload };
    case 'SET_BRUSH':
      return { ...state, brushedRange: action.payload };
    case 'SET_SEARCH':
      return { ...state, searchTerm: action.payload };
    case 'TOGGLE_POINT': {
      const next = new Set(state.selectedPoints);
      next.has(action.payload) ? next.delete(action.payload) : next.add(action.payload);
      return { ...state, selectedPoints: next };
    }
    case 'RESET':
      return INITIAL_FILTERS;
    default:
      return state;
  }
}

// Derive filtered data ONCE, pass to all charts:
const filteredData = useMemo(() => {
  return rawData.filter(row => {
    if (filters.selectedCategory && row.category !== filters.selectedCategory) return false;
    if (filters.brushedRange) {
      const [min, max] = filters.brushedRange;
      if (row.value < min || row.value > max) return false;
    }
    if (filters.searchTerm &&
        !String(row.name).toLowerCase().includes(filters.searchTerm.toLowerCase()))
      return false;
    return true;
  });
}, [rawData, filters]);
```

**UX requirements:**
- Highlight selected, **dim** (opacity 0.15–0.3) unselected — never hide
- Active filter badges: `Category: Electronics ✕`
- Click-again to deselect (toggle behavior)
- "Clear all filters" button visible when any filter active
- Count indicator: "Showing 234 of 1,205 records"

---

## 3. BRUSHING & RANGE SELECTION

Click and drag to select a range on an axis.

**Recharts:**
```jsx
<LineChart data={data}>
  <Brush
    dataKey="date"
    height={40}
    stroke="#4e79a7"
    onChange={({ startIndex, endIndex }) => {
      dispatch({ type: 'SET_BRUSH',
        payload: [data[startIndex]?.date, data[endIndex]?.date] });
    }}
  />
</LineChart>
```

**D3:**
```jsx
useEffect(() => {
  const brush = d3.brushX()
    .extent([[0, 0], [width, height]])
    .on('end', (event) => {
      if (!event.selection) { dispatch({ type: 'SET_BRUSH', payload: null }); return; }
      const [x0, x1] = event.selection.map(xScale.invert);
      dispatch({ type: 'SET_BRUSH', payload: [x0, x1] });
    });
  const g = d3.select(brushRef.current);
  g.call(brush);
  return () => { g.on('.brush', null); };
}, [width, height, xScale, dispatch]);
```

**UX:** Visual handles, shaded region, double-click to reset, show range as text.

---

## 4. HOVER TOOLTIPS

Every data point must have a tooltip. No exceptions.

**Recharts custom tooltip:**
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
      fontFamily: "'DM Sans', system-ui",
    }}>
      <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{
          display: 'flex', justifyContent: 'space-between', gap: 16,
          color: entry.color, marginBottom: 2, fontSize: 12,
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

**D3 tooltip (container-relative positioning):**
```jsx
const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, data: null });

// In the D3 useEffect:
selection.on('mousemove', (event, d) => {
  const rect = svgRef.current.getBoundingClientRect();
  setTooltip({
    show: true,
    x: event.clientX - rect.left + 12,
    y: event.clientY - rect.top - 12,
    data: d,
  });
}).on('mouseleave', () => {
  setTooltip(prev => ({ ...prev, show: false }));
});

// Render as a React overlay, NOT a D3-appended div:
{tooltip.show && (
  <div style={{
    position: 'absolute', left: tooltip.x, top: tooltip.y,
    pointerEvents: 'none', /* critical — prevents flicker */
  }}>
    {/* tooltip content */}
  </div>
)}
```

**Rules:** Appear < 50ms. Flip near edges. `pointerEvents: 'none'`. Never obscure the hovered element.

---

## 5. SORTING & REORDERING

```jsx
/** @typedef {{ key: string; dir: 'asc' | 'desc' }} SortConfig */

function useSort(defaultKey = 'value', defaultDir = 'desc') {
  const [sortConfig, setSortConfig] = useState({ key: defaultKey, dir: defaultDir });

  const toggle = useCallback((key) => {
    setSortConfig(prev => ({
      key,
      dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc',
    }));
  }, []);

  const sorted = useCallback((data) =>
    [...data].sort((a, b) => {
      const mult = sortConfig.dir === 'asc' ? 1 : -1;
      const va = a[sortConfig.key], vb = b[sortConfig.key];
      if (va == null) return 1;
      if (vb == null) return -1;
      return mult * (va > vb ? 1 : va < vb ? -1 : 0);
    }),
  [sortConfig]);

  return { sortConfig, toggle, sorted };
}
```

**UX:** Arrow indicator (▲/▼). Animate bar reordering with CSS transition. Default descending.

---

## 6. SEARCH & TEXT FILTERING

```jsx
function useDebounced(value, delay = 150) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

// Usage:
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounced(searchTerm, 150);
// Pass debouncedSearch to the filter reducer
```

**UX:** Search icon, clear button (✕), highlight matches, result count, empty state.

---

## 7. TIME ANIMATION

Animate through temporal data. Play/pause/scrub.

```jsx
function useTimePlayer(steps) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (!playing) return;
    const ms = 800 / speed;
    const id = setInterval(() => {
      setIndex(prev => {
        if (prev >= steps.length - 1) { setPlaying(false); return prev; }
        return prev + 1;
      });
    }, ms);
    return () => clearInterval(id);
  }, [playing, speed, steps.length]);

  return {
    index, setIndex,
    playing, toggle: () => setPlaying(p => !p),
    speed, setSpeed,
    current: steps[index],
  };
}
```

**UX:** Play/pause, scrubber, time label, speed control (0.5× 1× 2×), optional loop.

---

## 8. DATA TABLE

Sortable, searchable, paginated table for "detail on demand".

**Core features:**
- Column header click → sort (with ▲/▼)
- Search bar filtering all text columns
- Pagination: 20 rows/page, prev/next
- Row click → highlight in linked charts
- Conditional formatting: color cells by value range
- Sticky header on scroll
- CSV export via Blob URL

**Export pattern:**
```jsx
const exportCSV = useCallback(() => {
  const headers = columns.map(c => c.label).join(',');
  const rows = filteredData.map(row =>
    columns.map(c => JSON.stringify(row[c.key] ?? '')).join(',')
  );
  const csv = [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), {
    href: url, download: 'export.csv'
  }).click();
  URL.revokeObjectURL(url);
}, [columns, filteredData]);
```

---

## 9. ZOOM & PAN

For dense scatter plots, long time series, geographic maps.

```jsx
useEffect(() => {
  const zoom = d3.zoom()
    .scaleExtent([1, 20])
    .on('zoom', (event) => {
      chartGroupRef.current.attr('transform', event.transform);
    });
  const svg = d3.select(svgRef.current);
  svg.call(zoom);

  resetRef.current = () =>
    svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);

  return () => { svg.on('.zoom', null); };
}, []);
```

**UX:** Scroll to zoom, drag to pan. "Reset zoom" button. Limit zoom extent.

---

## 10. ANNOTATIONS

Highlight specific data points with contextual labels.

```jsx
/** @typedef {{ x: string; y: number; label: string }} Annotation */

// In Recharts:
{annotations.map(a => (
  <ReferenceLine key={a.x} x={a.x} stroke="#e15759"
    strokeDasharray="4 4"
    label={{ value: a.label, position: 'top', fill: '#e15759', fontSize: 11 }} />
))}
```

**UX:** Subtle dashed line, positioned to avoid overlap, optional expand-on-hover.

---

## 11. SANKEY

Flow diagrams for conversion funnels, budget flows, data pipelines.
Uses `d3-sankey` (available via D3).

```jsx
import * as d3 from 'd3';

/**
 * @typedef {{ name: string }} SankeyNode
 * @typedef {{ source: number; target: number; value: number }} SankeyLink
 */

function SankeyChart({ nodes, links, width = 700, height = 400 }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // d3-sankey layout
    const sankey = d3.sankey()
      .nodeId(d => d.index)
      .nodeWidth(20)
      .nodePadding(12)
      .extent([[1, 1], [width - 1, height - 5]]);

    const graph = sankey({
      nodes: nodes.map(d => ({ ...d })),
      links: links.map(d => ({ ...d })),
    });

    const color = d3.scaleOrdinal(d3.schemeTableau10);

    // Links
    svg.append('g')
      .attr('fill', 'none')
      .selectAll('path')
      .data(graph.links)
      .join('path')
      .attr('d', d3.sankeyLinkHorizontal())
      .attr('stroke', d => color(d.source.name))
      .attr('stroke-width', d => Math.max(1, d.width))
      .attr('stroke-opacity', 0.4)
      .on('mouseover', function () { d3.select(this).attr('stroke-opacity', 0.7); })
      .on('mouseout', function () { d3.select(this).attr('stroke-opacity', 0.4); });

    // Nodes
    svg.append('g')
      .selectAll('rect')
      .data(graph.nodes)
      .join('rect')
      .attr('x', d => d.x0)
      .attr('y', d => d.y0)
      .attr('height', d => Math.max(1, d.y1 - d.y0))
      .attr('width', d => d.x1 - d.x0)
      .attr('fill', d => color(d.name))
      .attr('rx', 2);

    // Labels
    svg.append('g')
      .style('font-family', "'DM Sans', system-ui")
      .style('font-size', '11px')
      .selectAll('text')
      .data(graph.nodes)
      .join('text')
      .attr('x', d => (d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6))
      .attr('y', d => (d.y1 + d.y0) / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', d => (d.x0 < width / 2 ? 'start' : 'end'))
      .text(d => d.name);

    return () => { svg.selectAll('*').remove(); };
  }, [nodes, links, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
}
```

**Note:** `d3-sankey` is bundled with the D3 import available in artifacts. If it is
NOT available at runtime, fall back to a manual Sankey layout by computing node
positions and Bézier paths manually — see D3 source for the algorithm.

**UX:** Hover link → highlight path + show flow value in tooltip. Click node → filter.

---

## 12. FORCE

Network/relationship visualization using D3 force simulation.

```jsx
function ForceGraph({ nodes, edges, width = 700, height = 500 }) {
  const svgRef = useRef(null);
  const simRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const color = d3.scaleOrdinal(d3.schemeTableau10);

    // Clone data — D3 force mutates node objects
    const nodeData = nodes.map(d => ({ ...d }));
    const linkData = edges.map(d => ({ ...d }));

    const sim = d3.forceSimulation(nodeData)
      .force('link', d3.forceLink(linkData)
        .id(d => d.id)
        .distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(20));

    simRef.current = sim;

    const link = svg.append('g')
      .selectAll('line')
      .data(linkData)
      .join('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.value || 1));

    const node = svg.append('g')
      .selectAll('circle')
      .data(nodeData)
      .join('circle')
      .attr('r', d => d.size || 8)
      .attr('fill', d => color(d.group || 0))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .call(drag(sim));

    const label = svg.append('g')
      .style('font-family', "'DM Sans', system-ui")
      .style('font-size', '10px')
      .style('pointer-events', 'none')
      .selectAll('text')
      .data(nodeData)
      .join('text')
      .text(d => d.label || d.id)
      .attr('dx', 12)
      .attr('dy', '0.35em');

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('cx', d => d.x).attr('cy', d => d.y);
      label.attr('x', d => d.x).attr('y', d => d.y);
    });

    return () => { sim.stop(); svg.selectAll('*').remove(); };
  }, [nodes, edges, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
}

function drag(simulation) {
  return d3.drag()
    .on('start', (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    })
    .on('drag', (event, d) => {
      d.fx = event.x; d.fy = event.y;
    })
    .on('end', (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    });
}
```

**UX:** Drag nodes to rearrange. Hover node → highlight edges. Click node → show detail panel.
Zoom via D3 zoom (see §9). For large graphs (100+ nodes), reduce charge strength and
add a collision force.
