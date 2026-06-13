# Extraction Rules and Heuristics

> **Disclaimer.** No information within this document should be taken for
> granted. Any statement or premise not backed by a real logical definition
> or verifiable reference may be invalid, erroneous, or a hallucination.

## 1. Dimension Detection Patterns

### 1.1 From Tables

Engineering reports commonly present dimensions in tables. Patterns:

```
| Parameter | Value | Unit |       → Direct extraction
| OD        | 168.275 | mm |

| Parameter | Value | Source |     → Value may include unit inline
| OD (given) | 6.625 in |         → Parse "6.625 in" → value=6.625, unit=in
```

**Rules:**
- If a table has columns named "Parameter"/"Property"/"Symbol" +
  "Value"/"Dimension" + "Unit"/"Source", it is a dimension table.
- Parse numeric values, tolerances (±, +/−), and units from cells.
- If a cell contains a formula or computation (e.g., "160.8 − 12.4 = 148.4"),
  extract the result and mark source as "computed".

### 1.2 From Equations

LaTeX or plaintext equations in reports:

```
δ = (OD_liner - ID_host) / 2 = (156.7 - 155.575) / 2 = 0.5625 mm
```

**Rules:**
- Identify the final numeric result as the extracted value.
- Record the full equation as the source.
- Link variable names to previously extracted dimensions.

### 1.3 From Prose

Dimensions embedded in running text:

```
"The host pipe has an OD of 6.625 inches and a wall thickness of
0.250 inches."
```

**Rules:**
- Look for patterns: `<parameter> of <number> <unit>`
- Also: `<number>-<unit> <parameter>` ("6.625-in OD")
- Also: `<parameter> = <number> <unit>` ("OD = 168.275 mm")
- Assign lower confidence than table/equation sources.

### 1.4 From Drawing Callouts (PDF/Image)

Dimension callouts on technical drawings follow ISO 129 / ASME Y14.5:

```
────── 155.575 ──────     Linear dimension
∅168.275                   Diameter
R25.4                      Radius
6.35 ±0.05                 Bilateral tolerance
6.35 +0.10/-0.00           Unilateral tolerance
```

**Rules:**
- ∅ prefix → diameter type
- R prefix → radius type
- ± or +/− → tolerance
- Degree symbol (°) → angular type
- Leader line endpoint indicates the target entity

## 2. Part Identification

### 2.1 Naming Heuristics

Parts are identified by:
- Explicit callout: "Part 1: HDPE Liner", balloon numbers
- Section headers: "## 2.1 Host Steel Pipe (API 5L)"
- BOM entries: item numbers with descriptions
- Contextual references: "the liner", "the host pipe", "the end-ring"

**Rules:**
- Use the document's own names verbatim.
- If a part has multiple names ("host pipe" / "steel casing" / "outer
  pipe"), pick the most specific and note aliases.
- Assign `part_id` as snake_case of the primary name.

### 2.2 Material Detection

Materials are identified by:
- Standards: "API 5L", "ASTM A106", "PE100", "PE80"
- Generic types: "carbon steel", "HDPE", "stainless steel 316L"
- Trade names: "Aldyl A", "DRISCOPIPE"
- Property tables with E, ν, σ_y values

**Rules:**
- If a standard is given (e.g., "API 5L X52"), record as `designation`.
- If generic type is given, record as `type`.
- Extract any property values found into `properties`.
- If properties are temperature-dependent, note the temperature.

## 3. View Inference Logic

When the source document has no explicit views (common in engineering
reports), infer views from the assembly type:

### 3.1 Decision Tree

```
Is the assembly rotationally symmetric?
  ├── Yes: Is it long (L/D > 2)?
  │     ├── Yes: Generate CROSS_SECTION + LONGITUDINAL_SECTION
  │     └── No:  Generate CROSS_SECTION + PLAN
  └── No:  Is it planar (one dominant dimension much smaller)?
        ├── Yes: Generate PLAN + EDGE_VIEW
        └── No:  Generate ISOMETRIC + 2 ORTHOGRAPHIC projections
```

### 3.2 Pipe-in-Pipe Specific

For lined pipe systems (the most common case in this user's work):

**View 1: Cross-Section (Radial)**
- Shows concentric circles: host OD, host ID, liner OD, liner ID
- Hatch host wall with `steel` pattern (45° lines, tight spacing)
- Hatch liner wall with `hdpe` pattern (45° lines, wider spacing)
- Show centerline cross (dashed)
- Dimension: all diameters, wall thicknesses, interference δ

**View 2: Longitudinal Section (Axial)**
- Shows upper half of pipe-in-pipe, symmetric about centerline
- Horizontal centerline (chain-dashed)
- Rectangles for each wall
- Show liner-host interface (contact line)
- If end-rings present, show as thickened sections at pipe ends
- Dimension: lengths, wall thicknesses, end-ring width

**View 3: Detail — Interference Zone**
- Enlarged view of the liner-host interface region
- Exaggerated gap showing δ
- Dimension δ with leader lines
- Note: "Interference exaggerated for clarity"

## 4. Unit Handling

### 4.1 Detection Priority

1. Explicit unit in the value cell: "6.625 in" → inches
2. Column header: "Value (mm)" → millimeters
3. Document-level default: title block says "All dimensions in mm"
4. Standard-implied: API pipe sizes are in inches
5. Magnitude heuristic: a pipe OD of 6.625 is almost certainly
   inches, not mm (6.625 mm is too small for a pipe)

### 4.2 Conversion

If the document mixes units (common: inches for host, mm for liner):
- Record each value in its original unit.
- Add a second field `value_mm` or `value_in` with the conversion.
- The EDIS `meta.units` field indicates the canonical unit system.
  All view coordinates should use this system.

Conversion factors (exact):
- 1 in = 25.4 mm
- 1 ft = 304.8 mm
- 1 m = 1000 mm

## 5. Confidence Assignment

| Condition | Confidence |
|---|---|
| Value from explicit table + CAS-verified | high |
| Value from explicit table, unverified | high |
| Value computed from other extracted values | medium-high |
| Value from prose, unambiguous | medium |
| Value from prose, ambiguous context | low |
| Value assumed (not stated, inferred from defaults) | low |
| Value from OCR on a scanned document | medium (check for OCR errors) |
| Value conflicts between sources | low (flag both) |

## 6. Common Pitfalls

1. **Don't confuse nominal and actual.** "6-inch pipe" is nominal —
   the actual OD is 6.625 in (for NPS 6). Use the actual dimension
   if given; note the nominal for reference.

2. **Don't assume WT is preserved through processes.** Swaging,
   drawing, rolling, and forming all change wall thickness. If the
   document flags this as unverified, propagate the flag.

3. **Watch for pre-process vs. post-process dimensions.** A liner may
   be 160.8 mm OD before swaging and 156.7 mm after reversion. These
   are different states of the same part.

4. **Don't conflate free and constrained dimensions.** A liner's free
   OD (unconstrained) vs. its in-situ OD (pressed against the host)
   are different values.

5. **Temperature matters.** HDPE dimensions change significantly with
   temperature (α ≈ 150×10⁻⁶/°C). If the reference temperature is
   unknown, flag it.
