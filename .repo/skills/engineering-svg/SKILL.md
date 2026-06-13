---
name: engineering-svg
description: >
  Produce standards-aware 2D engineering schematics and technical drawings
  as SVG files. Use whenever the user asks to draw, diagram, sketch, or
  illustrate any engineering concept needing dimensional accuracy, standard
  symbols, line weights, hatching, or annotation: cross-sections, P&IDs,
  electrical circuits, structural details, assembly views, hydraulic circuits,
  mechanical details, weld callouts, tolerance annotations, or any figure for
  an engineering report or standards submission. Also trigger when asked to
  "visualize" or "show" a mechanical, structural, civil, electrical, or
  process concept as a technical drawing (not infographic or UI). Trigger on
  casual phrasing: "draw the cross-section", "sketch the pipe layout", "show
  the interference fit", "diagram the circuit". If the output needs dimension
  lines, section hatching, or engineering symbols — use this skill.
---

# Engineering SVG Skill v0.1.0

Produce 2D engineering schematics as standards-aware SVG files.

## Before You Begin

1. Read `references/conventions.md` — it contains line-weight
   standards, hatching rules, dimensioning conventions, symbol
   libraries, and the SVG template structure. Do not guess conventions
   from memory; confirm against the reference.

---

## What This Skill Is

A structured method for producing **technical 2D drawings** as SVG
files that respect engineering drawing conventions. The output should
look like something a drafter would produce in a CAD system — not like
an infographic, not like a UI mockup, not like generative art.

## What This Skill Is NOT

- **Not a CAD system.** No parametric constraints, no 3D, no assembly
  trees, no BOM automation. The output is a static SVG image.
- **Not dimensionally exact to fabrication tolerance.** SVG coordinates
  are logical, not physical. The drawing communicates *intent and
  proportion* — it is not a manufacturing instruction unless the user
  explicitly provides all dimensions and the drawing is verified.
- **Not a replacement for FEA or simulation visualization.** Stress
  contours, flow fields, and deformation plots require specialized
  tools.

State these limitations to the user if they appear to expect more than
the skill delivers.

---

## Phase 0 — Classify the Drawing Type

Before drawing anything, determine which class of engineering drawing
is being requested. Each class has different conventions.

| Class | Examples | Key conventions |
|-------|----------|----------------|
| `cross_section` | Pipe cross-section, beam section, wall assembly | Hatching (material-specific), cutting-plane line, section label (A-A), hidden lines |
| `schematic_process` | P&ID, process flow diagram, hydraulic circuit | Standard instrument/valve symbols (ISA 5.1 / ISO 14617), flow arrows, tag annotations |
| `schematic_electrical` | Circuit diagram, single-line diagram, ladder logic | IEC 60617 / IEEE 315 symbols, wire numbering, terminal labels |
| `detail_mechanical` | Weld detail, fastener detail, tolerance callout | GD&T frames (ISO 1101 / ASME Y14.5), weld symbols (AWS A2.4 / ISO 2553), surface finish |
| `assembly` | Exploded view, cutaway, general arrangement | Part numbering (balloons), BOM reference, section views |
| `structural` | Connection detail, reinforcement layout, foundation plan | Dimension chains, grid lines, member labels, load arrows |
| `layout` | Pipe routing, cable tray layout, equipment arrangement | Scale bar, north arrow (if plan view), equipment tags, centerlines |
| `diagram_general` | Free-body diagram, force diagram, mechanism sketch | Force arrows with magnitude labels, pin/roller/fixed supports, motion arrows |

If the request doesn't fit neatly, pick the closest class and note
the deviation. If genuinely ambiguous, ask the user.

---

## Phase 1 — Gather Inputs

### Mandatory (must have before drawing)

| Input | If not provided |
|-------|----------------|
| **What to draw** — the physical system or concept | Cannot proceed — ask. |
| **Drawing class** (from Phase 0) | Infer from context; confirm with user if ambiguous. |
| **Key dimensions** — at minimum the proportions | Use the user's data. If no data, state that the drawing is *schematic / not to scale* and annotate it as such. |

### Optional (use if provided, use sensible defaults if not)

| Input | Default |
|-------|---------|
| Orientation (landscape / portrait) | Landscape for most; portrait for tall sections |
| Sheet size | A3 equivalent (420 × 297 mm logical) |
| Scale | "Not to scale" unless user provides dimensions |
| Standard family (ISO / ASME / company-specific) | ISO by default; ASME if user context is US/API |
| Color scheme | Monochrome (black on white) with standard color coding for specific domains (e.g., red for fire protection piping) |

---

## Phase 2 — Construct the SVG

### 2.1 Template Structure

Every engineering SVG must use the following layer structure.
Layers are implemented as SVG `<g>` elements with `id` attributes.

```
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <!-- 0. Background and border -->
  <g id="layer-border">...</g>

  <!-- 1. Title block (bottom-right per ISO 7200) -->
  <g id="layer-titleblock">...</g>

  <!-- 2. Drawing geometry — the actual engineering content -->
  <g id="layer-geometry">
    <!-- Sub-layers as needed -->
    <g id="layer-geometry-visible">...</g>
    <g id="layer-geometry-hidden">...</g>
    <g id="layer-geometry-centerline">...</g>
    <g id="layer-geometry-hatching">...</g>
  </g>

  <!-- 3. Dimensions and annotations -->
  <g id="layer-dimensions">...</g>

  <!-- 4. Notes, legends, callouts -->
  <g id="layer-notes">...</g>

  <!-- 5. Symbols (valves, instruments, electrical, etc.) -->
  <g id="layer-symbols">...</g>
</svg>
```

### 2.2 Coordinate System

- Origin at **top-left** (SVG default).
- All coordinates in logical units. 1 unit = 1 mm at the declared
  scale (or arbitrary if "not to scale").
- Use `viewBox` for scaling. Never use absolute pixel widths.
- Maintain **aspect ratio** — engineering drawings must not be
  distorted.

### 2.3 Line Conventions

See `references/conventions.md §2` for the full line-weight table.
Summary of the critical rules:

| Line type | SVG `stroke-width` | `stroke-dasharray` | Use |
|-----------|--------------------|--------------------|-----|
| Visible outline | 0.7 | — (solid) | Object edges visible to viewer |
| Hidden line | 0.35 | `6,3` | Edges behind the cutting plane or obscured |
| Centerline | 0.25 | `12,3,3,3` | Axes of symmetry, bolt circles, pipe centerlines |
| Dimension / leader | 0.25 | — (solid) | Dimension lines, extension lines, leaders |
| Cutting plane | 1.0 | `18,3` | Section cut indicator (with arrows at ends) |
| Phantom / alternate position | 0.25 | `12,3,3,3,3,3` | Ghost positions, adjacent parts for context |
| Break line | 0.35 | zigzag (path) | Indicates shortened/broken views |

All strokes default to `stroke: #000` (black). Use `stroke-linecap:
round` for dimension lines and `butt` for geometry.

### 2.4 Hatching

Hatching indicates cut material in section views. The pattern
identifies the material class.

| Material class | Pattern | Angle | Spacing | Reference |
|---|---|---|---|---|
| Metal (general) | Thin parallel lines | 45° | 2–3 mm | ISO 128-50 |
| Steel (specific) | Thin parallel lines | 45° | 1.5–2 mm | — |
| Concrete | Dots + irregular dashes | — | — | ISO 128-50 |
| Earth / soil | Random short dashes | — | — | — |
| Plastic / polymer (e.g., HDPE) | Thin parallel lines | 45° + cross-hatch at 135° | 3–4 mm | ISO 128-50 |
| Insulation | Wavy lines | — | — | — |
| Wood | Grain-like curves | along grain | — | — |
| Rubber / elastomer | Dots | — | 2 mm | — |

**Rules:**
- Hatching lines are thin (0.18–0.25 stroke-width).
- Adjacent parts in the same section must have different hatch angles
  or spacings to distinguish them.
- Never hatch over dimension text or annotations.
- Use SVG `<pattern>` elements for efficiency; define once in `<defs>`.

### 2.5 Dimensioning

Follow ISO 129-1 (or ASME Y14.5 if US context):

- **Extension lines** extend from the feature, with a small gap
  (~1.5 mm) from the object outline.
- **Dimension lines** run between extension lines, with arrowheads
  (or ticks for architectural).
- **Dimension text** is placed above the dimension line (ISO) or
  centered in a break in the line (ASME), reading from the bottom
  or right side.
- **Leader lines** connect callouts to features at 30°–60° angles,
  with an arrowhead at the feature end and a horizontal shoulder
  at the text end.
- **Arrowheads** are filled triangles, length ≈ 3× stroke-width,
  aspect ratio ~3:1.

Use `references/conventions.md §4` for the SVG path patterns for
arrowheads, GD&T frames, and weld symbols.

### 2.6 Text

- **Font:** Use a monospaced or engineering-style font. In SVG, use
  `font-family: 'Courier New', 'Liberation Mono', monospace` as a
  portable default. State in a note that the intended font is
  ISO 3098 / ASME Y14.2 style lettering.
- **Size:** Dimension text: 3.5 mm. Notes: 3.5 mm. Title block:
  5–7 mm for title, 3.5 mm for other fields.
- **Orientation:** All text must be readable from the bottom or right
  edge (ISO first-angle convention). Never upside-down, never reading
  from the left.

### 2.7 Title Block

Include a simplified ISO 7200 title block in the bottom-right corner.

Fields:
- Title (drawing name)
- Drawing number (or "SCHEMATIC" if informal)
- Scale (or "NOT TO SCALE")
- Date
- Projection symbol (first-angle or third-angle)
- Units (mm unless stated otherwise)
- Revision
- Source / disclaimer

If the drawing is schematic and produced by an LLM, the title block
**must** include a disclaimer: "LLM-generated schematic — verify
independently before use."

### 2.8 Symbols

For standard engineering symbols (valves, instruments, electrical
components), see `references/conventions.md §6–§8`.

**Critical rule:** Do not invent symbols. If the standard symbol for
a component is not in the reference, state this to the user and either
(a) use a generic rectangle with a text label, or (b) ask the user to
describe or provide the symbol.

---

## Phase 3 — Validate

Before outputting the SVG, check:

| # | Check | Action if fails |
|---|-------|-----------------|
| 1 | All visible edges use correct line weight | Fix stroke-width |
| 2 | Hidden lines are dashed, not solid | Fix stroke-dasharray |
| 3 | Centerlines use center-dash pattern | Fix |
| 4 | Hatching matches material class | Fix pattern |
| 5 | Adjacent hatched regions are distinguishable | Change angle/spacing |
| 6 | All dimensions have extension lines + arrowheads | Add missing elements |
| 7 | No dimension text overlaps geometry or other text | Reposition |
| 8 | Title block is present and filled | Add |
| 9 | "NOT TO SCALE" is stated if no scale is declared | Add note |
| 10 | LLM disclaimer is in title block | Add |
| 11 | SVG `viewBox` preserves aspect ratio | Fix |
| 12 | All `<text>` elements have `font-family` set | Fix |

---

## Phase 4 — Output

1. Save the SVG to `/home/claude/{descriptive-name}.svg`.
2. Copy to `/mnt/user-data/outputs/`.
3. Present to user via `present_files`.
4. In the chat message, briefly describe:
   - What the drawing shows
   - What conventions were followed
   - What is schematic vs. dimensionally accurate
   - Any symbols or features that could not be represented

---

## Domain-Specific Guidance

### Cross-Sections (e.g., pipe-in-pipe, structural members)

- Always show the cutting-plane line on a companion view if both views
  are present.
- Hatch all cut surfaces. Leave internal cavities (bores, voids)
  unhatched.
- For concentric cylinders (liner inside host), use different hatch
  angles for each material.
- Annotate radii, wall thicknesses, and interference/clearance gaps.
- If the section is axisymmetric, consider showing only a half-section
  with a centerline, to save space and emphasize the symmetry.

### P&ID / Process Schematics

- Use ISA 5.1 instrument bubbles (circle with horizontal line for
  field-mounted, square for panel-mounted).
- Use ISO 14617 or ISA standard valve symbols.
- Flow direction arrows on every pipe line.
- Pipe-line numbering: tag each line segment.
- Equipment shapes: simplified outlines (rectangles for vessels,
  circles for tanks, triangles for filters, etc.).

### Electrical Schematics

- Use IEC 60617 or IEEE 315 symbols.
- Wires as horizontal/vertical segments only (Manhattan routing).
- Junction dots (filled circles) where wires connect; no dot = crossing
  without connection.
- Component designators (R1, C2, U3, etc.) adjacent to each symbol.

### Free-Body / Mechanism Diagrams

- Force arrows: thick (0.7), with magnitude and direction labels.
- Support symbols: pin (triangle on line), roller (triangle on
  circles), fixed (hatched wall).
- Moment arrows: curved with direction.
- Clearly separate the FBD from the physical sketch if both are shown.

---

## Known Limitations

1. **SVG is 2D.** Isometric and perspective views can be faked but are
   not true projections. State this when producing them.
2. **No parametric constraints.** Moving one feature does not
   automatically update related dimensions.
3. **Symbol fidelity is approximate.** LLM-drawn SVG paths for standard
   symbols are close but not CAD-grade. Always include the disclaimer.
4. **Complex assemblies degrade.** Beyond ~20–30 distinct parts, the
   SVG becomes unwieldy and error-prone. Recommend splitting into
   multiple sheets.
5. **Font rendering varies.** The user's SVG viewer may substitute
   fonts. Recommend converting text to paths for archival use (not
   done automatically here).
6. **This skill does not verify engineering correctness.** It draws
   what it is told to draw. If the input data is wrong, the drawing
   will be wrong. The disclaimer in the title block exists for this
   reason.
