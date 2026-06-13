# Engineering Drawing Interchange Schema (EDIS) v0.1.0

> **Disclaimer.** No information within this document should be taken for
> granted. Any statement or premise not backed by a real logical definition
> or verifiable reference may be invalid, erroneous, or a hallucination.

## Purpose

EDIS is the intermediate JSON format that connects the
**eng-drawing-extractor** skill (producer) to the
**eng-schematic-renderer** skill (consumer). It captures the
engineering content of a document — geometry, dimensions, materials,
tolerances, assembly relationships — in a structured form that can be
rendered as technical schematics.

## Design Principles

1. **Extraction-first.** Fields that cannot be extracted are omitted,
   not guessed. Every value carries a `source` annotation.
2. **Render-ready.** Every geometric entity has enough information to
   draw it. Abstract concepts (material grade, tolerance class) travel
   as annotations, not geometry.
3. **View-centric.** Engineering drawings are organized by views
   (plan, section, detail, isometric). The schema mirrors this.
4. **Unit-explicit.** Every dimensional value carries its unit.

---

## Top-Level Structure

```jsonc
{
  "edis_version": "0.1.0",
  "meta": { /* Title block / document metadata */ },
  "parts": [ /* Part definitions */ ],
  "views": [ /* Drawing views, each with geometry + annotations */ ],
  "bom": [ /* Bill of materials entries */ ],
  "notes": [ /* General notes extracted from the document */ ],
  "unknowns": [ /* Items detected but not classifiable */ ]
}
```

---

## `meta` — Document Metadata / Title Block

```jsonc
{
  "title": "string",
  "drawing_number": "string | null",
  "revision": "string | null",
  "date": "ISO-8601 date | null",
  "author": "string | null",
  "scale": "string | null",         // e.g., "1:2", "NTS"
  "units": "mm | in | m",           // Default unit system
  "standard": "string | null",      // e.g., "API 5L", "ASME Y14.5"
  "source_document": "string",      // Filename or path of origin
  "extraction_confidence": "high | medium | low",
  "extraction_notes": ["string"]    // Caveats, ambiguities
}
```

---

## `parts` — Part Definitions

Each distinct component referenced in the drawing. Parts are
referenced by `part_id` from geometry entities and BOM entries.

```jsonc
{
  "part_id": "string",              // Unique within this EDIS instance
  "name": "string",                 // e.g., "HDPE Liner", "Steel Host Pipe"
  "material": {
    "designation": "string | null",  // e.g., "PE100", "API 5L X52"
    "type": "string | null",         // e.g., "HDPE", "carbon steel"
    "properties": {                  // Known mechanical properties
      "E": { "value": "number | null", "unit": "MPa | GPa", "temp": "string | null" },
      "nu": { "value": "number | null" },
      "alpha": { "value": "number | null", "unit": "1/°C | 1/K" },
      "yield": { "value": "number | null", "unit": "MPa" },
      "density": { "value": "number | null", "unit": "kg/m³" }
    },
    "source": "string"              // Where this data came from
  },
  "geometry_summary": {
    "type": "cylinder | plate | ring | profile | complex",
    "OD": { "value": "number | null", "unit": "mm | in" },
    "ID": { "value": "number | null", "unit": "mm | in" },
    "WT": { "value": "number | null", "unit": "mm | in" },
    "length": { "value": "number | null", "unit": "mm | m | in" }
  },
  "notes": ["string"],
  "source": "string"
}
```

---

## `views` — Drawing Views

Each view represents a distinct projection or section. Views contain
geometric entities and annotations (dimensions, labels, symbols).

```jsonc
{
  "view_id": "string",
  "type": "cross_section | longitudinal_section | plan | elevation | detail | isometric | schematic",
  "title": "string | null",
  "description": "string | null",
  "scale": "string | null",
  "coordinate_system": {
    "origin": "string",            // Description: "pipe centerline", "left end"
    "x_axis": "string",           // e.g., "axial", "radial", "horizontal"
    "y_axis": "string"            // e.g., "radial", "axial", "vertical"
  },
  "entities": [ /* GeometryEntity[] */ ],
  "dimensions": [ /* Dimension[] */ ],
  "annotations": [ /* Annotation[] */ ],
  "section_cut": {                 // Only for section views
    "plane": "string",            // e.g., "A-A", "longitudinal through centerline"
    "location": "string | null"
  }
}
```

### GeometryEntity

Primitives that can be drawn. Every entity references its parent part.

```jsonc
{
  "entity_id": "string",
  "part_id": "string",            // FK → parts[].part_id
  "type": "line | arc | circle | rectangle | polygon | path | hatch | centerline | hidden_line",
  "role": "outline | hidden | centerline | hatch | construction | phantom | dimension_leader",

  // --- Type-specific fields (include only the relevant set) ---

  // line
  "start": { "x": "number", "y": "number" },
  "end": { "x": "number", "y": "number" },

  // arc
  "center": { "x": "number", "y": "number" },
  "radius": "number",
  "start_angle": "number",        // degrees
  "end_angle": "number",

  // circle
  "center": { "x": "number", "y": "number" },
  "radius": "number",

  // rectangle
  "origin": { "x": "number", "y": "number" },  // bottom-left
  "width": "number",
  "height": "number",
  "corner_radius": "number | 0",

  // polygon
  "points": [{ "x": "number", "y": "number" }],

  // path (SVG-compatible)
  "d": "string",                  // SVG path data

  // hatch
  "boundary": "string",           // entity_id of bounding entity or "polygon" with points
  "pattern": "steel | hdpe | concrete | general | section",
  "angle": "number | 45",
  "spacing": "number | null",

  // Style
  "stroke_style": "solid | dashed | dotted | dashdot | phantom",
  "stroke_weight": "thin | medium | thick",
  "label": "string | null"
}
```

### Dimension

Extracted dimensional callouts.

```jsonc
{
  "dim_id": "string",
  "type": "linear | diameter | radius | angular | ordinate | arc_length",
  "value": "number",
  "unit": "mm | in | deg",
  "tolerance": {
    "type": "bilateral | unilateral | limit | basic | reference | null",
    "upper": "number | null",
    "lower": "number | null",
    "fit_class": "string | null"   // e.g., "H7/p6"
  },
  "from_entity": "string | null",  // entity_id
  "to_entity": "string | null",    // entity_id
  "label": "string | null",        // As written on drawing: "∅155.575"
  "source": "string"
}
```

### Annotation

Non-dimensional text, symbols, callouts.

```jsonc
{
  "annotation_id": "string",
  "type": "note | label | callout | gdt_frame | weld_symbol | surface_finish | balloon | flag",
  "text": "string",
  "position": { "x": "number", "y": "number" } | null,
  "points_to": "string | null",    // entity_id it references
  "source": "string"
}
```

---

## `bom` — Bill of Materials

```jsonc
{
  "item_number": "number | string",
  "part_id": "string",            // FK → parts[].part_id
  "description": "string",
  "quantity": "number",
  "material": "string | null",
  "specification": "string | null",
  "notes": "string | null"
}
```

---

## `notes` — General Notes

```jsonc
{
  "note_id": "string",
  "category": "general | process | inspection | material | tolerance | assembly | safety",
  "text": "string",
  "applies_to": ["string"],       // part_ids or "all"
  "source": "string"
}
```

---

## `unknowns` — Unclassified Extractions

Items the extractor detected but could not confidently classify.
The renderer should ignore these; they exist for human review.

```jsonc
{
  "raw_text": "string",
  "context": "string",            // Where in the document it appeared
  "guess": "string | null",       // Best-effort classification
  "confidence": "low"
}
```

---

## Source Annotation Convention

Every extracted value should include a `source` field (string) that
traces where the value came from. Format:

```
"§2.1, table row 'OD (given)'"
"page 3, dimension callout near section A-A"
"computed: OD - 2×WT = 155.575"
"assumed: WT unchanged after swaging (flagged as unverified)"
```

This is critical for downstream validation — the renderer can display
provenance, and humans can audit the extraction.

---

## Extraction Completeness Markers

The extractor must include a completeness assessment:

```jsonc
{
  "completeness": {
    "parts_extracted": "number",
    "parts_expected": "number | null",
    "views_generated": "number",
    "dimensions_extracted": "number",
    "coverage": "full | partial | minimal",
    "missing": ["string"],         // Known gaps
    "confidence": "high | medium | low"
  }
}
```

---

## Versioning

EDIS uses semver. The `edis_version` field in the top-level object
is the schema version. Both the extractor and renderer must check
this field and warn on version mismatch.

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0   | Draft  | Initial schema covering pipes, cylinders, sections |
