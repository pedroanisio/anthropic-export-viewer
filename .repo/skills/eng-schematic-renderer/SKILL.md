---
name: eng-schematic-renderer
description: >
  Render engineering schematics — cross-sections, longitudinal sections,
  detail views, assembly drawings — from structured EDIS JSON data
  produced by the eng-drawing-extractor skill. Produces standards-
  compliant technical drawings as inline SVG (via Visualizer),
  interactive React artifacts, or downloadable SVG/PDF files. Trigger
  whenever the user asks to "render the schematic", "draw the cross-
  section", "visualize the assembly", "show me the pipe layout",
  "generate a technical drawing", "render the EDIS", "make a section
  view", or any variation of producing a visual engineering drawing
  from extracted data. Also trigger when the eng-drawing-extractor
  has produced an EDIS JSON and the user wants to see it. Even casual
  phrasing like "show me what this looks like" or "draw it" after an
  extraction should trigger this skill. If EDIS JSON is not available
  but the user wants a schematic from a document, trigger
  eng-drawing-extractor first, then this skill.
---

# Engineering Schematic Renderer

Render technical engineering schematics from EDIS (Engineering Drawing
Interchange Schema) JSON data. Produces dimensioned cross-sections,
longitudinal sections, detail views, and assembly drawings that follow
drafting standards (ISO 128 / ASME Y14).

## Before You Begin

1. **Read the EDIS schema** — `references/edis-schema.md` defines the
   input format. Understand every field before rendering.

2. **Read the rendering rules** — `references/rendering-rules.md`
   contains line styles, hatching, dimension placement, color palette,
   layout conventions, and interactive feature specs. Follow them.

---

## Core Workflow

### Phase 1 — Acquire and Validate EDIS Input

**Option A: EDIS file exists.** Read it from the path provided by the
extractor (typically `/home/claude/edis_output.json`).

**Option B: EDIS embedded in conversation.** Parse it from the
conversation context.

**Option C: No EDIS available.** Tell the user you need structured data
first. Suggest running `eng-drawing-extractor` on their document.

**Validate** the EDIS before rendering (see `references/rendering-rules.md`
§8). Report any issues.

### Phase 2 — Plan the Layout

Examine the EDIS `views[]` array. For each view:

1. Compute the bounding box from entity coordinates.
2. Determine aspect ratio and scale.
3. Assign a position in the multi-view layout grid.

Layout rules from `references/rendering-rules.md` §1.2:
- Cross-sections: square, left side.
- Longitudinal sections: wide, right side.
- Details: below, independently scaled.
- Title block: bottom-right, always present.

If the EDIS has a single view, center it with generous margins.

### Phase 3 — Render Geometry

For each view, render entities in this order (back to front):

1. **Hatch fills** — Render filled areas first so outlines draw on top.
2. **Hidden lines** — Dashed lines for hidden edges.
3. **Visible outlines** — Solid lines for visible edges.
4. **Centerlines** — Chain-dashed, extending slightly past the geometry.
5. **Construction lines** — Thin, if any.

**Entity type → SVG mapping:**

| Entity Type | SVG Element |
|---|---|
| `line` | `<line x1 y1 x2 y2>` |
| `arc` | `<path d="M... A...">` (SVG arc command) |
| `circle` | `<circle cx cy r>` |
| `rectangle` | `<rect x y width height rx>` |
| `polygon` | `<polygon points>` |
| `path` | `<path d>` (pass through) |
| `hatch` | `<rect>` or `<polygon>` with `fill="url(#hatch-pattern)"` |
| `centerline` | `<line>` with dash-array `20,4,4,4` |
| `hidden_line` | `<line>` with dash-array `8,4` |

Apply styles from `references/rendering-rules.md` §2.

### Phase 4 — Render Dimensions

After geometry, overlay dimensions:

1. Read `dimensions[]` from the view.
2. Compute extension line positions from the referenced entities.
3. Place dimension lines, arrowheads, and text.
4. Follow placement rules from `references/rendering-rules.md` §4.

**Dimension text formatting:**
- Linear: `155.575` (no prefix)
- Diameter: `∅155.575`
- Radius: `R25.4`
- Angular: `45°`
- With tolerance: `6.35 ±0.05`
- Reference: `(148.4)` (parenthetical)

Use monospace font for dimension text. Size: 3–4% of view height.

### Phase 5 — Render Annotations

After dimensions:

1. Part labels — bold, near the part, with leaders if needed.
2. Material callouts — smaller text near part labels.
3. Section indicators — thick lines with letters + arrows.
4. Notes — numbered, in a notes block.
5. Title block — bottom-right.

### Phase 6 — Choose Output Mode

Based on complexity and context:

| Condition | Output Mode |
|---|---|
| ≤2 views, ≤20 entities, conversational | Visualizer inline SVG |
| >2 views or >20 entities or interactive features needed | React artifact (.jsx) |
| User asks for downloadable file | SVG file → `/mnt/user-data/outputs/` |
| User asks for print-ready | PDF via pdf skill |

For the Visualizer path:
1. Call `visualize:read_me` with module `["diagram"]`.
2. Build the SVG string following the rules.
3. Call `visualize:show_widget` with the SVG.

For the React artifact path:
1. Build a React component with SVG rendering + interactive features.
2. Create it as `.jsx` in `/mnt/user-data/outputs/`.
3. Include hover info, dimension toggles, and data panel
   (see `references/rendering-rules.md` §6).

---

## Rendering Recipes

### Recipe 1: Pipe-in-Pipe Cross-Section

The most common rendering for lined pipe systems.

**Input:** EDIS with ≥2 cylindrical parts (host + liner).

**Steps:**
1. Extract OD and ID for each part.
2. Draw concentric circles, largest first.
3. Apply material-specific hatch to each annular region.
4. Add centerline cross (horizontal + vertical chain-dashed).
5. Dimension all diameters (outside the outermost circle).
6. Dimension wall thicknesses (between adjacent surfaces).
7. Label each part and its material.

**Coordinate computation:**
```
For each part (host, liner, etc.):
  outer_radius = OD / 2
  inner_radius = ID / 2
  center = (0, 0)  // All concentric, centered on origin

SVG viewBox: computed from host OD + margin for dimensions
  extent = host_OD * 1.6  // 60% margin for dimensions and labels
  viewBox = `-extent/2 -extent/2 extent extent`
```

### Recipe 2: Pipe-in-Pipe Longitudinal Section

**Input:** EDIS with cylindrical parts + axial length.

**Steps:**
1. Draw centerline (horizontal, y=0, full width).
2. For each part, draw upper-half wall as a rectangle:
   - y_inner = ID/2, y_outer = OD/2
   - x_start = 0, x_end = length (or proportional)
3. Mirror for lower half.
4. Hatch each wall region.
5. If interference fit, show the contact interface as a bold line.
6. If end-rings present, draw as thickened rectangles at pipe ends.
7. Dimension wall thicknesses, diameters (via leader), and length.

### Recipe 3: Interference Detail

**Input:** EDIS with interference dimensions (δ, ΔD).

**Steps:**
1. Zoom into the liner-host interface region.
2. Draw the host inner surface (straight line, top).
3. Draw the liner outer surface (straight line, bottom) with an
   exaggerated gap representing δ.
4. Add a dimension for δ between the two surfaces.
5. Use `--eng-interference` color for the gap and dimension.
6. Add note: "Gap exaggerated for clarity. Actual δ = <value> mm."
7. Optionally show the contact pressure direction with arrows.

### Recipe 4: Generic Part Cross-Section

**Input:** EDIS with a single part of any type.

**Steps:**
1. Determine the part's cross-sectional shape from `geometry_summary.type`.
2. Draw the outline.
3. Apply appropriate hatch for the material.
4. Dimension the key features.
5. Label the part.

---

## SVG Template

All SVGs follow this base structure:

```xml
<svg viewBox="X Y W H" xmlns="http://www.w3.org/2000/svg"
     font-family="monospace" font-size="14">
  <defs>
    <!-- Hatch patterns -->
    <pattern id="hatch-steel" ...>...</pattern>
    <pattern id="hatch-hdpe" ...>...</pattern>
    <!-- Arrowhead marker -->
    <marker id="arrowhead" markerWidth="8" markerHeight="6"
            refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="var(--eng-dimension)"/>
    </marker>
    <marker id="arrowhead-rev" markerWidth="8" markerHeight="6"
            refX="0" refY="3" orient="auto">
      <polygon points="8 0, 0 3, 8 6" fill="var(--eng-dimension)"/>
    </marker>
  </defs>

  <style>
    .outline { stroke: var(--eng-outline, #1a1a1a); fill: none;
               stroke-width: 2; }
    .hidden  { stroke: var(--eng-hidden, #666); fill: none;
               stroke-width: 1; stroke-dasharray: 8 4; }
    .center  { stroke: var(--eng-centerline, #cc0000); fill: none;
               stroke-width: 0.7; stroke-dasharray: 20 4 4 4; }
    .dim     { stroke: var(--eng-dimension, #0044aa); fill: none;
               stroke-width: 0.7; }
    .dim-text { fill: var(--eng-dimension, #0044aa);
                font-family: monospace; font-size: 12px;
                text-anchor: middle; }
    .label   { fill: var(--eng-outline, #1a1a1a);
               font-family: sans-serif; font-size: 14px;
               font-weight: bold; }
    .note    { fill: var(--eng-annotation, #006633);
               font-family: sans-serif; font-size: 11px; }
    .title-block { stroke: var(--eng-outline, #1a1a1a);
                   fill: none; stroke-width: 1.5; }
  </style>

  <!-- GEOMETRY GROUP -->
  <g id="geometry">
    <!-- Hatches, then hidden, then outlines, then centerlines -->
  </g>

  <!-- DIMENSIONS GROUP -->
  <g id="dimensions">
    <!-- Extension lines, dimension lines, text -->
  </g>

  <!-- ANNOTATIONS GROUP -->
  <g id="annotations">
    <!-- Labels, callouts, notes -->
  </g>

  <!-- TITLE BLOCK -->
  <g id="title-block" transform="translate(...)">
    <!-- Border, title, metadata -->
  </g>
</svg>
```

---

## Error Handling

| Situation | Action |
|---|---|
| EDIS is missing or invalid | Report validation errors. Suggest re-running extractor. |
| View has no coordinates (only semantic descriptions) | Attempt to generate coordinates from `geometry_summary`. If not possible, report. |
| Too many entities for Visualizer | Switch to React artifact mode. |
| Dimension references non-existent entity | Skip that dimension, log warning. |
| Parts overlap in unexpected ways | Render as-is, add a warning note. |

---

## Reminder

The rendering rules in `references/rendering-rules.md` are the
authoritative visual standard. Every line style, hatch pattern,
dimension format, and layout convention is defined there. Consult it
for any rendering decision. The EDIS schema in `references/edis-schema.md`
defines the input contract. Do not accept or produce non-conformant data.
