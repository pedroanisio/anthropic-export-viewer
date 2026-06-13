---
name: eng-drawing-extractor
description: >
  Extract structured engineering drawing data from documents — PDFs,
  images, markdown reports, specs, datasheets — and produce EDIS JSON
  (Engineering Drawing Interchange Schema) for the eng-schematic-renderer
  skill. Trigger on "extract drawing data", "pull dimensions from",
  "parse engineering specs", "get geometry from this document", "extract
  parts and dimensions", "prepare data for a schematic", "read this
  drawing", "extract BOM", "pull tolerances", or any request to convert
  engineering documents into structured data. Also trigger when a user
  uploads a technical PDF or engineering report and asks to "visualize",
  "draw", "make a schematic", or "render the geometry" — run this
  extractor first, then hand off to eng-schematic-renderer. Even casual
  "what does this part look like" or "draw this pipe" on an engineering
  document should trigger this skill as step one.
---

# Engineering Drawing Extractor

Extract engineering content from documents into the **EDIS** (Engineering
Drawing Interchange Schema) format — a structured JSON that captures
parts, geometry, dimensions, materials, tolerances, and assembly
relationships.

## Before You Begin

1. **Read the EDIS schema** — `references/edis-schema.md` defines every
   field, type, and convention. Read it before extracting anything.
   The schema is the contract with downstream consumers (especially
   `eng-schematic-renderer`). Do not invent fields.

2. **Read the extraction heuristics** — `references/extraction-rules.md`
   contains domain-specific rules for identifying parts, dimensions,
   and views from different document types.

---

## Core Workflow

### Phase 1 — Classify the Source Document

Before extracting, determine what kind of document you're working with.
This drives the extraction strategy.

| Document Type | Primary Extraction Method | Expected Yield |
|---|---|---|
| **Engineering report** (Markdown, DOCX) | Parse tables, equations, and prose for dimensions, materials, tolerances | Parts + dimensions + materials; views must be inferred |
| **Technical drawing** (PDF with vector graphics) | Extract dimension callouts, title block, BOM, section labels | Full: parts + views + dimensions + annotations |
| **Scanned drawing** (PDF image / photo) | OCR + spatial analysis of text positions relative to geometry | Partial: depends on scan quality |
| **Specification / datasheet** | Parse tables and structured text for properties and limits | Parts + materials + tolerances; geometry may be minimal |
| **3D model export** (STEP, IGES metadata) | Extract feature tree, dimensions from metadata | Parts + geometry summary; no 2D views |

**If the document type is ambiguous, state your classification and
confidence before proceeding.**

### Phase 2 — Extract Parts

Identify every distinct physical component mentioned in the document.
For each part:

1. **Name it** — use the document's own terminology. Do not rename.
2. **Assign a `part_id`** — short, snake_case, unique. E.g.,
   `steel_host_pipe`, `hdpe_liner`, `end_ring`.
3. **Extract material** — look for:
   - Explicit material callouts ("API 5L X52", "PE100")
   - Material property tables (E, ν, α, σ_y)
   - Process-implied materials ("swaged HDPE")
4. **Extract geometry summary** — OD, ID, WT, length, shape type.
5. **Log the source** — where in the document each value came from.

**Rules:**
- If a value is computed (e.g., ID = OD − 2×WT), mark the source as
  `"computed: OD - 2×WT = <value>"` and trace the inputs.
- If a value is assumed (e.g., WT unchanged after swaging), mark it as
  `"assumed: <reason>"` and set confidence to `low` or `medium`.
- If a value is missing, omit the field — do not guess.

### Phase 3 — Extract or Infer Views

Engineering documents may contain explicit views (section drawings,
detail callouts) or may require you to infer appropriate views from
the described geometry.

**Explicit views:** Extract them directly. Look for:
- Section labels ("Section A-A", "Detail B")
- Scale callouts
- Projection indicators (first-angle, third-angle)
- Coordinate system references

**Inferred views (from reports/specs):** Generate logical views based
on the part geometry:

| Geometry Type | Default Views to Generate |
|---|---|
| Concentric cylinders (pipe-in-pipe) | Cross-section (radial) + longitudinal section |
| Plate / flat part | Plan view + edge view |
| Ring / annular part | Cross-section + plan view |
| Complex assembly | Exploded view + assembled cross-section |

For each view:

1. **Define the coordinate system** — origin, axes, and what they mean
   physically.
2. **Generate geometry entities** — translate dimensions into drawable
   primitives (lines, arcs, circles, rectangles).
3. **Assign roles** — outline, centerline, hidden line, hatch.
4. **Position entities** — use extracted dimensions to compute
   coordinates. All coordinates should be in the document's unit system.

### Phase 4 — Extract Dimensions and Tolerances

For every dimensional value found in the document:

1. **Classify it** — linear, diameter, radius, angular, etc.
2. **Record the numeric value and unit.**
3. **Extract any tolerance** — bilateral (±), unilateral, limit,
   fit class (H7/p6), GD&T frame.
4. **Link it to geometry** — which entity or entities does this
   dimension span?
5. **Preserve the label** — record the dimension as written on the
   drawing (e.g., "∅155.575", "6.35 ±0.05").

### Phase 5 — Extract Annotations, BOM, and Notes

- **Annotations**: GD&T frames, weld symbols, surface finish callouts,
  balloon numbers, flags.
- **BOM**: Item numbers, part references, quantities, material specs.
- **Notes**: General notes, process notes, inspection requirements,
  safety callouts.

Classify each note by category (general, process, inspection, material,
tolerance, assembly, safety).

### Phase 6 — Assess Completeness

Before producing the final EDIS JSON:

1. **Count what you extracted** vs. what you expected to find.
2. **List known gaps** — dimensions you couldn't find, views you
   couldn't infer, parts mentioned but not dimensioned.
3. **Rate overall confidence** — high / medium / low.
4. **Log unknowns** — anything detected but not classifiable.

---

## Coordinate Generation Rules

When generating entity coordinates for inferred views (Phase 3),
follow these conventions:

### Cross-Section View (Radial Cut)

For concentric cylinders, draw from outside in:

```
Origin: geometric center of outermost cylinder
X-axis: horizontal (left = negative)
Y-axis: vertical (up = positive)

Outer cylinder: circle at origin, radius = OD_outer/2
Inner surface of outer cylinder: circle at origin, radius = ID_outer/2
Outer surface of inner cylinder: circle at origin, radius = OD_inner/2
Inner surface of inner cylinder: circle at origin, radius = ID_inner/2
```

Apply hatching between inner and outer surfaces of each part (different
hatch patterns per material).

### Longitudinal Section View

For pipe-in-pipe assemblies:

```
Origin: left end of assembly, at centerline
X-axis: axial direction (right = positive)
Y-axis: radial direction (up = positive from centerline)

Draw upper half only (symmetric about centerline), then mirror.
Centerline: horizontal dashed line at y=0.
```

Each wall appears as a rectangle:
- Outer pipe upper wall: rectangle from (0, ID_host/2) to (L, OD_host/2)
- Liner upper wall: rectangle from (0, ID_liner/2) to (L, OD_liner/2)

### Dimension Placement

- **Diameters**: Place outside the largest circle, with leader lines.
- **Wall thicknesses**: Dimension between adjacent surfaces.
- **Radial interference (δ)**: Show as a detail with exaggerated gap.
- **Axial dimensions**: Place above or below the longitudinal view.

---

## Output

Produce a single EDIS JSON file. Save it as:
```
/home/claude/edis_output.json
```

Then either:
- Present it to the user for review, or
- Hand it off to `eng-schematic-renderer` if the user asked for a
  visual output.

### Handoff Protocol

When handing off to the renderer, provide:
1. The EDIS JSON file path.
2. A brief summary: how many parts, how many views, confidence level.
3. Any renderer hints:
   - Preferred view to render first
   - Whether to show dimensions
   - Whether to show hatching
   - Scale preference

---

## Domain-Specific Extraction Rules

### Pipe-in-Pipe / Lined Pipe Systems

These are the most common use case (interference fits, swaged liners,
CRA-lined pipe). Special rules:

- **Interference**: Compute δ, ΔD, r from extracted diameters. Show
  these as derived dimensions in the EDIS.
- **Pre/post process states**: If the document describes a part in
  multiple states (pre-swage vs. post-reversion), create separate
  geometry summaries or dimension sets, labeled by state.
- **Contact interface**: The interface between liner and host is a
  critical feature. Mark it explicitly as an annotation.

### Pressure Vessels / Cylindrical Shells

- Extract design pressure, MAWP, hydrostatic test pressure.
- Identify longitudinal and circumferential stress directions.
- Look for corrosion allowance dimensions.

### Structural Steel

- Extract section designations (W12×26, HSS 6×4×3/8).
- Connection details: bolt patterns, weld callouts, plate sizes.
- Identify load paths from member annotations.

### Flanges and Fittings

- Extract flange class, face type, bolt circle diameter.
- Gasket dimensions and material.
- Bore/hub dimensions.

---

## Error Handling

| Situation | Action |
|---|---|
| Document is unreadable (corrupt PDF, blank image) | Report failure. Do not fabricate data. |
| Dimensions conflict (OD in text ≠ OD in table) | Extract both, flag conflict in `extraction_notes`. |
| Units ambiguous (bare "6.625" — inches or mm?) | Infer from context (API 5L → inches). State assumption. |
| Part referenced but never dimensioned | Create part entry with `geometry_summary: null`. List in `missing`. |
| Document contains multiple independent assemblies | Create separate EDIS instances or clearly partition views by assembly. |

---

## Reminder

The EDIS schema in `references/edis-schema.md` is the authoritative
contract. Every field you produce must conform to it. Every value must
carry a `source` annotation. Never fabricate dimensions — if you cannot
extract a value, omit it and log the gap.
