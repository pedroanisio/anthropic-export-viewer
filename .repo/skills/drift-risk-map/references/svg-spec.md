# SVG Visual Specification

Layout rules, color system, typography, and construction patterns for the
drift-risk map SVG. Read this before Phase 5.

---

## Table of Contents

1. [Canvas and dimensions](#1-canvas-and-dimensions)
2. [Color system](#2-color-system)
3. [Typography](#3-typography)
4. [Section 1: Header and stat cards](#4-section-1-header-and-stat-cards)
5. [Section 2: Hub-and-spoke diagram](#5-section-2-hub-and-spoke-diagram)
6. [Section 3: Coupling inventory table](#6-section-3-coupling-inventory-table)
7. [Section 4: Mitigations](#7-section-4-mitigations)
8. [Section 5: Footer](#8-section-5-footer)
9. [Adaptive layout rules](#9-adaptive-layout-rules)
10. [SVG boilerplate](#10-svg-boilerplate)

---

## 1. Canvas and dimensions

The SVG canvas is 1400px wide. Height is variable — compute it from the
content after all sections are laid out. Use `viewBox="0 0 1400 H"` where
H is the total computed height.

Safe content area: `x=70` to `x=1330` (1260px usable width), `y=20` top
padding.

Section spacing: 30px gap between major sections. Use horizontal rules
(`<line>` at 0.5px stroke, color `#e0ddd5`) to separate sections.

Background: single `<rect>` covering the full canvas, `fill="#FAFAF8"`.
This gives a warm off-white that reads as neutral in both screen and
print contexts.

Target file size: under 50KB. SVG text is verbose — keep label strings
short and avoid duplicating data that is already in the table rows.

## 2. Color system

Four risk tiers, each with a consistent 4-stop ramp (background, border,
badge, text). Every color in the SVG must come from this table or from
the neutral palette below it. Do not invent colors.

### Risk tier ramps

| Tier | Background | Border/Stroke | Badge fill | Text |
|------|-----------|---------------|-----------|------|
| P0 CRITICAL | `#FEF3EF` | `#F0997B` | `#D85A30` | `#712B13` (title) / `#993C1D` (body) |
| P1 HIGH | `#FDF6E9` | `#FAC775` | `#BA7517` | `#633806` (title) / `#854F0B` (body) |
| P2 MODERATE | `#EDF4FC` | `#85B7EB` | `#378ADD` | `#042C53` (title) / `#185FA5` (body) |
| P3 LOW | `#E9F7F0` | `#5DCAA5` | `#1D9E75` | `#04342C` (title) / `#0F6E56` (body) |

### Neutral palette

| Use | Color |
|-----|-------|
| Page background | `#FAFAF8` |
| Section divider lines | `#e0ddd5` |
| Primary text (titles, headings) | `#1a1a1a` |
| Secondary text (subtitles, descriptions) | `#666` |
| Tertiary text (metadata, hints) | `#888` |
| Mono/code text | `#555` |
| Disclaimer text | `#999` |
| Table header background | `#EEEDEE` |
| Table header text | `#555` |
| Hub fill (center node) | `#534AB7` (purple) |
| Hub stroke | `#3C3489` |
| Hub text | `#fff` |

### Risk ring fills (concentric circles)

Each risk ring uses a radial gradient from the tier's badge color at low
opacity. Define as `<linearGradient>` with two stops:

| Ring | Start opacity | End opacity |
|------|-------------|------------|
| P0 (innermost) | 0.12 | 0.03 |
| P1 | 0.08 | 0.02 |
| P2 | 0.06 | 0.01 |
| P3 (outermost) | 0.05 | 0.01 |

Ring strokes: same badge color, 0.4px, `stroke-dasharray="6 4"`.

### Connector line styles

Lines connecting spoke nodes to the hub encode risk via weight and style:

| Tier | Stroke color | Width | Style | Opacity |
|------|-------------|-------|-------|---------|
| P0 | `#D85A30` | 2.5px | solid | 0.5 |
| P1 | `#BA7517` | 1.8px | solid | 0.4 |
| P2 | `#378ADD` | 1.2px | solid | 0.35 |
| P3 | `#1D9E75` | 0.8px | dashed (`4 3`) | 0.35 |

All connectors use `marker-end="url(#arr)"` for arrowheads.

## 3. Typography

Import IBM Plex Sans and IBM Plex Mono from Google Fonts inside a
`<style>` block in `<defs>`. These fonts render well in SVG across
browsers and design tools.

```xml
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap');
  text { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }
</style>
```

### Text classes (define in `<style>`)

| Class | Size | Weight | Fill | Use |
|-------|------|--------|------|-----|
| `.title` | 28px | 600 | `#1a1a1a` | Page title |
| `.subtitle` | 15px | 400 | `#666` | Page subtitle |
| `.section-title` | 18px | 600 | `#1a1a1a` | Section headings |
| `.section-sub` | 13px | 400 | `#888` | Section subtitles |
| `.hub-label` | 22px | 600 | `#fff` | Center hub text |
| `.hub-sub` | 13px | 400 | `rgba(255,255,255,0.8)` | Hub subtitle |
| `.node-title` | 13px | 500 | (per tier) | Spoke node titles |
| `.node-sub` | 11px | 400 | (per tier) | Spoke node subtitles |
| `.ring-label` | 11px | 500 | (per tier, reduced opacity) | P0/P1/P2/P3 labels on rings |
| `.stat-num` | 32px | 600 | (per tier) | Stat card numbers |
| `.stat-label` | 11px | 500 | `#888` | Stat card labels |
| `.badge-text` | 10px | 600 | `#fff` | Text inside badge pills |
| `.cell-head` | 11px | 500 | `#555` | Table header cells |
| `.cell-text` | 11px | 400 | `#333` | Table body cells |
| `.cell-mono` | 10px | 400 | `#555` | Table monospace cells |
| `.fix-label` | 11px | 600 | `#333` | Mitigation labels |
| `.fix-text` | 11px | 400 | `#444` | Mitigation descriptions |
| `.disclaimer` | 10px | 400 | `#999` | Footer disclaimer |

Use `text-anchor="middle"` + `dominant-baseline="central"` for text
centered in boxes. Use `text-anchor="start"` for left-aligned table cells.

## 4. Section 1: Header and stat cards

Starts at `y=20`. Contains:

1. **Title line** — project name, class `.title`, at `x=70`.
2. **Subtitle line** — summary stats (coupling count, generator count,
   type count, crate count — whatever top-level numbers are relevant),
   class `.subtitle`, 24px below the title.
3. **Divider line** — full-width at `y ≈ title_bottom + 16`.
4. **Four stat cards** — horizontally arranged, each 150×72px, `rx=10`,
   18px gap between them. Starting at `x=70`, `y = divider + 18`.

Each stat card:
- Fill: tier background color.
- Stroke: tier border color, 0.5px.
- Large number: class `.stat-num`, fill = tier text (title shade), left-
  aligned at `x=card_x+20`.
- Label: class `.stat-label`, fill = tier text (title shade), to the
  right of the number.
- Sublabel: 10px, tier body text shade, below the label.

If a tier has 0 couplings, still show the card — the zero is informative.

## 5. Section 2: Hub-and-spoke diagram

This is the core visual. It occupies roughly 700px of vertical space
(adjust based on node count).

### Identifying the hub

The hub is the primary source of truth that fans out to the most
dependents. In most codebases this is one artifact (e.g., the AST, the
OpenAPI spec, the Prisma schema, the domain model). If the codebase has
two clear hubs with independent fan-outs, use two hub nodes side by side.
Do not use more than two hubs — if the topology is that distributed,
the hub-and-spoke model is not the right visual and you should fall back
to a grid layout (see section 9).

Hub node:
- Circle, `r=42`, fill = `#534AB7`, stroke = `#3C3489`, stroke-width
  1.5px.
- Label inside: class `.hub-label` + `.hub-sub`, white, centered.
- Positioned at the center of the diagram group.

### Risk rings

Four concentric dashed circles centered on the hub. Radii increase
in roughly equal steps — suggested values for a 700px-tall section:

| Ring | Radius | Represents |
|------|--------|-----------|
| P0 | 120px | Critical — innermost |
| P1 | 195px | High |
| P2 | 270px | Moderate |
| P3 | 340px | Low — outermost |

Each ring:
- `fill="url(#ring-pN)"` (the gradient defined in defs).
- Stroke: tier badge color, 0.4px, `stroke-dasharray="6 4"`.
- Opacity: P0=0.6, P1=0.5, P2=0.4, P3=0.35.

Place a small tier label (class `.ring-label`) just outside each ring
at 3 o'clock, e.g. `x = hub_cx + radius + 6`.

### Spoke nodes

Each coupling from the inventory becomes a spoke node, positioned on
the ring corresponding to its risk tier.

Node construction:
- Rounded rect, 130–150px wide × 48px tall, `rx=8`.
- Fill: tier background color.
- Stroke: tier badge color, stroke-width varies by tier (1px for P0,
  0.8px for P1, 0.7px for P2, 0.5px for P3).
- Title: class `.node-title`, tier title text color, centered.
- Subtitle: class `.node-sub`, tier body text color, centered, 16px
  below title.
- Badge pill below the rect: small rect (44–56px × 16px), `rx=4`,
  filled with tier badge color, white badge text centered.

### Node placement strategy

Distribute nodes around the hub to minimize connector crossings:

1. Count nodes per ring.
2. Spread them evenly around the ring's arc. For rings with 2 nodes,
   place them at 10 and 2 o'clock (roughly ±45° from top). For 3 nodes,
   use 10, 12, and 2 o'clock. For 4 nodes, use 10, 11, 1, 2 o'clock.
3. If two rings have nodes at the same angle, offset one by ±15° to
   avoid radial overlap.
4. Verify no spoke node's rect overlaps another node's rect. If they
   do, widen the angular spread or stagger radially.

### Connectors

Draw a line from each spoke node's nearest edge to the hub circle's
perimeter. Use the connector style from the color system table (section
2). All connectors carry the arrow marker pointing toward the hub to
indicate "dependency direction" (dependent → source of truth).

Compute start and end points so lines touch the node rect edge and the
hub circle perimeter, not the centers — this avoids lines hiding under
shapes.

## 6. Section 3: Coupling inventory table

A full SVG-rendered table mirroring the Markdown inventory. Place it
below the hub diagram, separated by a section divider.

### Table structure

- **Header row**: 26px tall, `#EEEDEE` fill, `rx=4`. Column headers in
  class `.cell-head`.
- **Data rows**: 44–52px tall depending on whether the row has one or
  two lines of text. Alternate background tint: use the tier background
  color at 0.5–0.7 opacity for a subtle band.

### Columns

| Column | x offset | Width | Content |
|--------|---------|-------|---------|
| # | 10 | 24px | Row number, `.cell-text` bold |
| Relationship | 34 | 276px | Title + subtitle (mono), two lines |
| Mechanism | 310 | 220px | `.cell-mono` |
| Guard | 530 | 300px | `.cell-text` + `.cell-mono` subtitle |
| Propagation | 830 | 150px | `.cell-text`, color-coded per tier |
| Priority | 980 | 80px | Badge pill (tier badge fill, white text) |
| Risk | 1060 | 200px | `.cell-text`, tier text color, bold for CRIT/HIGH |

### Row heights

- Single-line rows (short descriptions): 44px.
- Two-line rows (title + mono subtitle): 52px.
- P0 rows get a distinct tint (`#FEF8F5` at 0.7 opacity) so they
  visually pop even in a long table.

Compute total table height from the number of rows and their individual
heights. Leave 20px below the table before the next section.

## 7. Section 4: Mitigations

Render the top-N remediation recommendations from Phase 3 (up to 5). Use
one card per mitigation:

- Rect: full content width (1260px) × 40px, `rx=6`.
- Fill: tier background color.
- Stroke: tier border color, 0.4px.
- Badge pill inside at the left edge: tier badge fill, white text.
- Fix label: class `.fix-label`, bold, immediately after the badge.
- Fix description: class `.fix-text`, to the right of the label.

Stack cards with 8px vertical gap. Order by priority (P0 first).

## 8. Section 5: Footer

A single divider line followed by the disclaimer:

```
This diagram was produced by static heuristic analysis. No finding
should be taken as ground truth. Validate all CRITICAL and HIGH
findings manually before acting on them.
```

Class `.disclaimer`, 17px below the divider. Leave 20px bottom margin.

## 9. Adaptive layout rules

### Small inventories (< 5 couplings)

If fewer than 5 couplings were found, the table section is compact
enough that the SVG can be shorter. Reduce ring radii by 20% and
section spacing by 10px. The hub-and-spoke still works down to 2
couplings — just position the two nodes at 10 and 2 o'clock on the
appropriate ring.

### Large inventories (> 15 couplings)

If more than 15 couplings were found:
- Increase canvas width to 1600px to give the table more room.
- Consider splitting the table into two sub-tables: one for CRITICAL+HIGH,
  one for MODERATE+LOW.
- In the hub diagram, if a single ring has > 5 nodes, split them across
  two radial offsets (inner and outer) within the same ring band, 30px
  apart.

### No clear single hub

If the codebase does not have one dominant source of truth (e.g., a
microservices repo where drift happens between services rather than from
a central schema), replace the hub-and-spoke diagram with a **grid
layout**:

- One card per coupling, arranged in a 3-column grid.
- Each card: 400×80px, tier-colored, containing the source, dependent,
  and risk badge.
- Sort by risk tier (CRITICAL top-left → LOW bottom-right).
- Draw connecting lines between cards that share an artifact (same file
  appears as source in one coupling and dependent in another).

This is the fallback — prefer hub-and-spoke whenever possible because
the concentric rings communicate risk hierarchy at a glance.

### Multiple outputs

If the user explicitly requests only the Markdown report or only the SVG,
honor that. If they request both (the default), produce both files in the
same directory and mention the companion file in each:
- The Markdown report's executive summary should note:
  "A visual overview is available in `drift-risk-map.svg`."
- The SVG's title subtitle should note the Markdown companion.

## 10. SVG boilerplate

Start every SVG with this skeleton. Replace `H` with the computed height,
`[Project Name]` with the actual project name, and fill in the sections.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 H" width="1400" height="H">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
            stroke-width="1.8" stroke-linecap="round"
            stroke-linejoin="round"/>
    </marker>

    <!-- Risk ring gradients -->
    <linearGradient id="ring-p0" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#D85A30" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#D85A30" stop-opacity="0.03"/>
    </linearGradient>
    <linearGradient id="ring-p1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#BA7517" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#BA7517" stop-opacity="0.02"/>
    </linearGradient>
    <linearGradient id="ring-p2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#378ADD" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#378ADD" stop-opacity="0.01"/>
    </linearGradient>
    <linearGradient id="ring-p3" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1D9E75" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#1D9E75" stop-opacity="0.01"/>
    </linearGradient>

    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap');
      text { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }
      .mono { font-family: 'IBM Plex Mono', monospace; }
      /* ... define all text classes from section 3 ... */
    </style>
  </defs>

  <!-- Background -->
  <rect width="1400" height="H" fill="#FAFAF8"/>

  <!-- Section 1: Header + stat cards -->
  <!-- ... -->

  <!-- Section 2: Hub-and-spoke diagram -->
  <g transform="translate(700, hub_cy)">
    <!-- Risk rings, connectors, hub, spoke nodes -->
  </g>

  <!-- Section 3: Coupling inventory table -->
  <g transform="translate(70, table_y)">
    <!-- Table header + rows -->
  </g>

  <!-- Section 4: Mitigations -->
  <g transform="translate(70, mitigations_y)">
    <!-- Mitigation cards -->
  </g>

  <!-- Section 5: Footer -->
  <line x1="70" y1="footer_y" x2="1330" y2="footer_y"
        stroke="#e0ddd5" stroke-width="0.5"/>
  <text class="disclaimer" x="70" y="footer_y + 17">
    This diagram was produced by static heuristic analysis...
  </text>
</svg>
```

Use `<g transform="translate(x, y)">` for each major section to keep
coordinates local and make vertical repositioning easy. Compute each
section's y-offset from the height of the section above it plus the
30px gap.

### Construction order

Build the SVG in this order to correctly compute heights:

1. Lay out the header — fixed height (~195px with stat cards).
2. Lay out the hub diagram — height depends on outermost ring radius
   × 2 + padding (~720px typical).
3. Lay out the table — height = header(26) + sum of row heights + 20.
4. Lay out mitigations — height = N × 48 + 10.
5. Footer — 40px.
6. Sum all section heights + gaps → set as viewBox height.
