# Rendering Rules for Engineering Schematics

> **Disclaimer.** No information within this document should be taken for
> granted. Any statement or premise not backed by a real logical definition
> or verifiable reference may be invalid, erroneous, or a hallucination.

## 1. General SVG Layout

### 1.1 Canvas

All schematics are rendered as SVG with these defaults:

```
viewBox: computed from geometry extents + margins
Default margins: 15% of geometry extent on each side
Font family: monospace for dimensions, sans-serif for labels
Background: transparent (inherits from container)
```

Use CSS variables from the Visualizer `read_me` if rendering inline,
or define a self-contained palette if producing a standalone file.

### 1.2 Multi-View Layout

When rendering multiple views from a single EDIS:

```
┌─────────────────────────────────────────────┐
│  Cross-Section View        Longitudinal View │
│  (left, square)            (right, wide)     │
├─────────────────────────────────────────────┤
│  Detail View(s)            Title Block       │
│  (bottom-left)             (bottom-right)    │
└─────────────────────────────────────────────┘
```

**Rules:**
- Cross-section views are square (1:1 aspect).
- Longitudinal views are wide (3:1 to 6:1 aspect, depending on L/D).
- Detail views go below, scaled independently.
- Title block: bottom-right corner, always present.

### 1.3 Scale

Compute scale automatically:
1. Find the bounding box of all entities in a view.
2. Fit to the allocated canvas area with margins.
3. Display the scale factor (e.g., "Scale 1:5") in the view title.

For detail views, use a larger scale (typically 2× to 5× the parent).

---

## 2. Line Styles (ISO 128 / ASME Y14.2)

| Role | Stroke | Width | Dash Pattern |
|---|---|---|---|
| `outline` (visible edges) | Solid | 0.7mm equiv | `none` |
| `hidden` (hidden edges) | Dashed | 0.35mm equiv | `8,4` |
| `centerline` | Chain-dashed | 0.25mm equiv | `20,4,4,4` |
| `construction` | Thin solid | 0.18mm equiv | `none` |
| `phantom` | Long-dashed | 0.35mm equiv | `20,4,4,4,4,4` |
| `dimension_leader` | Thin solid | 0.25mm equiv | `none` |
| `hatch` | Thin solid | 0.18mm equiv | `none` |
| `section_cut` | Extra thick | 1.0mm equiv | `none` |

**SVG stroke-width translation:** Use relative units based on the
view's scale. A good default is `outline` = 0.5% of viewBox width.

### Color Palette

For screen rendering (not print):

```css
--eng-outline: #1a1a1a;
--eng-hidden: #666666;
--eng-centerline: #cc0000;
--eng-dimension: #0044aa;
--eng-hatch-steel: #555555;
--eng-hatch-hdpe: #2266aa;
--eng-hatch-concrete: #888888;
--eng-annotation: #006633;
--eng-interference: #cc3300;
--eng-background: transparent;
```

For dark mode, invert by swapping light ↔ dark and adjusting saturation.
If using the Visualizer, use CSS variables (`var(--text-color)`, etc.)
and map the engineering palette onto them.

---

## 3. Hatching Patterns

Hatching indicates material in section views. Patterns follow ISO 128-50:

| Material | Pattern | Angle | Spacing | SVG Implementation |
|---|---|---|---|---|
| `steel` / `general` | Parallel lines | 45° | Tight (2–3px) | `<pattern>` with rotated `<line>` |
| `hdpe` / `plastic` | Parallel lines | 45° | Wide (5–6px) | Same, wider spacing |
| `concrete` | Gravel pattern | — | — | Dots + short random lines |
| `section` (generic) | Parallel lines | 45° | Medium (4px) | Default hatch |

**Rules:**
- Adjacent parts in section must have different hatch angles or patterns
  so they are visually distinguishable.
- If two adjacent parts are both steel, rotate one by 90° (use 135°).
- Hatch only the solid material, not voids.
- Leave a small gap (1–2px) between hatch and boundary line for clarity.

### SVG Hatch Pattern Template

```xml
<defs>
  <pattern id="hatch-steel" patternUnits="userSpaceOnUse"
           width="6" height="6" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="6"
          stroke="var(--eng-hatch-steel)" stroke-width="0.5"/>
  </pattern>
  <pattern id="hatch-hdpe" patternUnits="userSpaceOnUse"
           width="10" height="10" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="10"
          stroke="var(--eng-hatch-hdpe)" stroke-width="0.5"/>
  </pattern>
</defs>
```

---

## 4. Dimension Rendering

### 4.1 Anatomy of a Dimension

```
        extension line
           │
    ┌──────┤
    │      │
    │  ◄───┼──── 155.575 ────┼───►
    │      │                 │
    └──────┤                 ├──────┐
           │                 │      │
        extension line    extension line
```

Components:
- **Extension lines**: Thin lines extending from the entity to the
  dimension line. Gap of ~2px from entity, extend ~3px past dim line.
- **Dimension line**: Thin line between extension lines, with
  arrowheads (or ticks) at each end.
- **Dimension text**: Centered on or above the dimension line.
  Font: monospace, sized for readability (typically 3–4% of viewBox).
- **Arrowheads**: Filled triangles, ~8px long, ~3px wide.

### 4.2 Diameter Dimensions

For circles in cross-section views:

```
          ∅155.575
     ◄──────────────►
    ╱                  ╲
   ╱                    ╲
  │                      │
   ╲                    ╱
    ╲                  ╱
```

- Leader line passes through circle center.
- Text outside the circle, with ∅ prefix.
- Arrow touches the circle circumference on both sides.

### 4.3 Wall Thickness Dimensions

For pipe walls in longitudinal section:

```
    ┌────────────────────────────┐  ← outer surface
    │ ↕ 6.35                     │
    ├────────────────────────────┤  ← inner surface
    │                            │
```

- Short linear dimension, perpendicular to the wall.
- Place outside the wall if space permits; inside with leader if not.

### 4.4 Interference Dimension (δ)

Special treatment for interference fits:

- Show an exaggerated gap between the two surfaces.
- Use a distinct color (`--eng-interference`).
- Label with the symbol δ and the value.
- Add a note: "Gap exaggerated for clarity."

### 4.5 Placement Priority

When dimensions crowd, prioritize (highest first):
1. Critical dimensions (OD, ID, WT of primary parts)
2. Interface dimensions (δ, ΔD, clearances)
3. Secondary dimensions (lengths, radii)
4. Reference dimensions (parenthetical, informational)

If space is tight, move lower-priority dimensions to a separate
detail view or a dimension table.

---

## 5. Annotations

### 5.1 Labels and Callouts

- Part labels: Bold text, positioned near the part, with a leader
  line if the text is far from the part.
- Material callouts: Smaller text below the part label.
- Notes: Numbered, placed in a note block outside the views.

### 5.2 Section Indicators

For section cuts shown in one view with the section displayed in another:

```
   A ──────────────── A
   ▼                  ▼
```

- Thick line with letters at each end.
- Arrows indicating viewing direction.
- Section view labeled "Section A-A".

### 5.3 Title Block

Every schematic must have a title block containing:
- Drawing title (from `meta.title`)
- Drawing number and revision (if available)
- Scale
- Units
- Date
- Source document reference
- Extraction confidence level
- **"SCHEMATIC — NOT FOR FABRICATION"** warning

---

## 6. Interactive Features (HTML/React Renderer)

When rendering as an interactive widget (via the Visualizer or as a
React artifact), add these features:

### 6.1 Hover Information

On hover over any entity:
- Show part name, material, and relevant dimensions.
- Highlight all dimensions associated with that part.

### 6.2 Dimension Toggle

Checkbox controls to show/hide dimension categories:
- [ ] All dimensions
- [ ] Diameters
- [ ] Wall thicknesses
- [ ] Tolerances
- [ ] Reference dimensions

### 6.3 View Tabs

If multiple views exist, render them as tabs or a grid that the
user can reorganize.

### 6.4 Zoom and Pan

For complex drawings, enable:
- Scroll-to-zoom on the SVG viewport.
- Click-and-drag pan.
- Reset-to-fit button.

### 6.5 Data Panel

Collapsible side panel showing:
- Parts list with material and dimensions.
- Extraction confidence indicators.
- Source traceability for any selected dimension.

---

## 7. Output Modes

The renderer supports multiple output modes:

| Mode | Tool | Output | Use Case |
|---|---|---|---|
| **Inline SVG** | Visualizer `show_widget` | SVG in chat | Quick visualization during conversation |
| **Interactive HTML** | React artifact (.jsx) | Standalone app | Complex drawings, user interaction needed |
| **Static SVG file** | `create_file` → .svg | Downloadable file | For embedding in reports |
| **PDF drawing** | `create_file` → .pdf (via pdf skill) | Print-ready | Formal deliverable |

**Default:** Use the Visualizer for inline SVG if the drawing has ≤2
views and ≤20 entities. Use a React artifact for anything more complex.

---

## 8. Validation Before Rendering

Before generating any visual output, validate the EDIS input:

1. **Schema version**: Check `edis_version` matches "0.1.x".
2. **Parts referenced**: Every `part_id` in entities exists in `parts[]`.
3. **Coordinates present**: Every geometric entity in a view has
   coordinates (not just semantic descriptions).
4. **Units consistent**: All coordinates use the same unit system.
5. **No NaN/null coordinates**: Skip entities with missing positions;
   log a warning.

If validation fails, report the issues to the user and offer to
re-run the extractor with fixes.
