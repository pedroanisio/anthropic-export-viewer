---
name: logo-to-svg
description: "Convert a raster logo image (PNG, JPG, BMP, WebP) into a high-fidelity SVG vector replica using computer vision, color quantization, and bitmap tracing. Use this skill whenever the user uploads a logo, icon, badge, emblem, wordmark, or any graphic and asks to vectorize it, trace it, convert it to SVG, recreate it as a vector, or make a scalable version. Also trigger when the user says 'turn this image into an SVG', 'make this logo a vector', 'trace this logo', 'SVG version of this', 'vectorize this', 'recreate as vector', 'I need this as an SVG', or anything involving raster-to-vector conversion of a graphic. The skill produces: (1) the SVG file, (2) the Python script that generated it, and (3) an overlay comparison image proving fidelity. Even if the user only says 'make an SVG from this image' without saying 'logo', use this skill — it works on any flat graphic."
---

# Logo-to-SVG Vectorization Skill

Convert any raster logo/graphic into a faithful SVG vector using a
computer-vision pipeline: color quantization, mask extraction,
bitmap tracing (potrace + OpenCV), and verification overlay.

## What this skill produces

Every run outputs **three files**:

| # | File | Purpose |
|---|------|---------|
| 1 | `<name>.svg` | The vector replica |
| 2 | `logo_to_svg.py` | The Python script that produced it (fully standalone) |
| 3 | `<name>_overlay.png` | Side-by-side comparison (original vs SVG render vs diff heatmap vs blended overlay) |

All three go to `/mnt/user-data/outputs/` for the user to download.

---

## Quick-start (most conversions)

```bash
# 0. Ensure dependencies
pip install svgwrite cairosvg scikit-learn --break-system-packages -q
apt-get install -y potrace -qq 2>/dev/null || true

# 1. Run the pipeline
python3 /path/to/scripts/logo_to_svg.py \
    /mnt/user-data/uploads/LOGO_FILE \
    -o /home/claude/logo_output.svg \
    --colors 8 \
    --detail medium \
    --overlay /home/claude/logo_overlay.png \
    --script-copy /home/claude/logo_to_svg_script.py

# 2. Copy outputs to user-visible directory
cp /home/claude/logo_output.svg      /mnt/user-data/outputs/
cp /home/claude/logo_overlay.png     /mnt/user-data/outputs/
cp /home/claude/logo_to_svg_script.py /mnt/user-data/outputs/
```

Then use `present_files` to share all three with the user.

---

## Full workflow — step by step

### Step 0: Inspect the uploaded image

Before running the pipeline, look at the image (it should be in your
context as a vision input) and decide on parameters:

- **Count approximate colors.**  A flat 3-color logo → `--colors 4`.
  A gradient-heavy emblem → `--colors 12-16`.
- **Check for fine text or thin strokes.**  If present → `--detail high`.
- **Check for transparency.**  PNGs with alpha → the pipeline handles
  it automatically (transparent regions are excluded from tracing).

If unsure, start with defaults (`--colors 8 --detail medium`) and
refine after inspecting the overlay.

### Step 1: Install dependencies

```bash
pip install svgwrite cairosvg scikit-learn --break-system-packages -q
apt-get install -y potrace -qq 2>/dev/null || true
```

These are usually already present, but the install commands are
idempotent and fast.

### Step 2: Run the conversion

The script lives at `scripts/logo_to_svg.py` relative to this
skill's directory.  Use its full path:

```python
# In a bash tool call:
python3 SKILL_DIR/scripts/logo_to_svg.py \
    INPUT_PATH \
    -o /home/claude/STEM.svg \
    --colors N \
    --detail LEVEL \
    --overlay /home/claude/STEM_overlay.png \
    --script-copy /home/claude/logo_to_svg.py
```

Replace:
- `SKILL_DIR` → the directory containing this SKILL.md
- `INPUT_PATH` → the uploaded file path (`/mnt/user-data/uploads/...`)
- `STEM` → a clean filename derived from the input
- `N` → color count from Step 0
- `LEVEL` → `low` | `medium` | `high`

### Step 3: Inspect the overlay

View the overlay PNG (`view` tool).  Check:

1. **Color accuracy** — Do the SVG colors match the original?
2. **Shape fidelity** — Are edges smooth?  Are curves preserved?
3. **Missing regions** — Are any parts of the logo absent?
4. **Artifacts** — Any stray speckles or merged regions?

The overlay's diff heatmap (third panel) highlights problem areas in
red.  Blue/black = good match.

### Step 4: Refine if needed

If the overlay reveals issues:

| Problem | Fix |
|---------|-----|
| Missing subtle colors | Increase `--colors` (e.g., 12 or 16) |
| Jagged edges on curves | Switch to `--method potrace` or increase `--detail` |
| Too much noise / speckles | Decrease `--detail` to `low` |
| Fine text is blobby | Set `--detail high` |
| SVG file is huge (>1MB) | Decrease `--colors`, use `--detail low` |

Re-run the script with adjusted parameters.  The overlay comparison
lets you objectively compare iterations.

### Step 5: Deliver outputs

Copy all three files to `/mnt/user-data/outputs/` and use
`present_files` to share them:

```bash
cp /home/claude/STEM.svg           /mnt/user-data/outputs/
cp /home/claude/STEM_overlay.png   /mnt/user-data/outputs/
cp /home/claude/logo_to_svg.py     /mnt/user-data/outputs/
```

Present the SVG first (primary deliverable), then mention the
overlay and the script.

---

## Pipeline internals (read if troubleshooting)

For deep technical details on each stage, read:
`references/techniques.md`

### Architecture summary

```
Input Image
    │
    ▼
[1] Preprocess (denoise, resize, alpha extraction)
    │
    ▼
[2] Color Quantization (K-Means → N color clusters)
    │
    ▼
[3] Per-color binary mask extraction + morphological cleanup
    │
    ▼
[4] Bitmap → Vector tracing
    ├── potrace (preferred: optimal Bézier curves)
    └── OpenCV Catmull-Rom→Bézier (fallback)
    │
    ▼
[5] SVG assembly (layered paths, evenodd fill, background rect)
    │
    ▼
[6] Overlay verification (cairosvg render → MSE/PSNR diff)
```

### Method selection logic

The script prefers **potrace** when the `potrace` binary is found on
`$PATH`.  Potrace produces mathematically optimal cubic Bézier curves
and smaller SVG files.  If potrace is unavailable or fails for a
specific layer, it falls back to **OpenCV Catmull-Rom Bézier tracing**
which is slightly less optimal but still produces smooth curves.

You can force a method with `--method potrace` or `--method opencv`.

### Known limitations

- **Gradients** are approximated as discrete color bands.  The
  pipeline does not emit SVG `<linearGradient>` or `<radialGradient>`
  elements.  For gradient-heavy logos, increasing `--colors` to
  12-16 produces a decent banded approximation.
- **Photographic content** (e.g., a photo inside a logo) is not
  suited for vectorization.  The skill works best on flat/semi-flat
  graphics.
- **Very fine text** at small sizes may lose legibility.  For logos
  where text fidelity is critical, consider tracing at `--detail high`
  and manually editing the SVG afterward.

---

## Parameter quick-reference

| Flag | Default | Range | Effect |
|------|---------|-------|--------|
| `--colors` | 8 | 2–32 | K-means cluster count |
| `--detail` | medium | low/medium/high | Morphological cleanup aggressiveness |
| `--tolerance` | 0.001 | 0.0001–0.01 | Douglas-Peucker epsilon (OpenCV only) |
| `--max-dim` | 2000 | 500–4000 | Resize cap for large images |
| `--method` | auto | potrace/opencv | Force tracing backend |
| `--overlay` | none | path | Write comparison PNG |
| `--script-copy` | none | path | Copy the .py script for the user |
