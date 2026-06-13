# Techniques Reference — logo-to-svg

## Table of Contents

1. [Color Quantization (K-Means)](#color-quantization)
2. [Morphological Mask Refinement](#morphological-refinement)
3. [Bitmap Tracing — Potrace](#potrace)
4. [Bitmap Tracing — OpenCV Contours](#opencv-contours)
5. [Catmull-Rom → Cubic Bézier Conversion](#bezier-conversion)
6. [Background Detection Heuristic](#background-detection)
7. [Overlay Verification Metrics](#overlay-metrics)
8. [Tuning Guide](#tuning-guide)

---

## Color Quantization

The pipeline uses `sklearn.cluster.KMeans` to reduce the image to N
dominant colors.  Each cluster center becomes one color layer in the
SVG.

**Why K-Means over median-cut / octree?**  For logo images (typically
≤ 12 distinct colors), K-Means gives tighter clusters and is fast
enough (< 2s for a 2000×2000 image on 8 clusters).

**Alpha handling:**  Pixels with alpha < 128 are excluded from
clustering entirely.  They receive no label and are not vectorized —
this preserves transparent regions without injecting noise into the
color model.

**`min_pixel_ratio`:**  Clusters covering < 0.5% of opaque pixels are
dropped.  This suppresses anti-aliased fringe colors that would
otherwise generate thousands of tiny speckle paths.

---

## Morphological Refinement

After quantization, each color-layer mask is cleaned with OpenCV
morphological operations:

- **Close** (dilation → erosion): fills small holes inside regions.
- **Open** (erosion → dilation): removes small isolated dots.

The kernel size is controlled by the `--detail` flag:

| Detail | Kernel | Effect |
|--------|--------|--------|
| low    | 5×5    | Aggressive smoothing — good for simple flat logos |
| medium | 3×3    | Balanced — default |
| high   | 1×1    | No morphology — preserves fine strokes/text |

---

## Potrace

[Potrace](http://potrace.sourceforge.net/) (Peter Selinger, 2001) is
the gold-standard bitmap tracer.  It operates on monochrome bitmaps
and produces optimal cubic Bézier curves.

**Pipeline integration:**  Each color layer's binary mask is saved as
a BMP (inverted: potrace treats black as foreground), potrace runs in
SVG output mode, and the `d="..."` attributes are extracted from the
resulting `<path>` elements.

**Key parameters the skill exposes:**

| Param          | Flag      | Effect |
|----------------|-----------|--------|
| turdsize       | `-t`      | Suppress regions < N pixels (speckle filter) |
| alphamax       | `-a`      | Corner threshold (0 = sharp corners, 1.334 = smooth) |
| opttolerance   | `-O`      | Bézier optimization tolerance (lower = tighter fit) |

If potrace is unavailable or fails, the pipeline falls back to
OpenCV contour tracing automatically.

---

## OpenCV Contours

Two sub-methods are available:

### 4b-i: Douglas-Peucker polygon approximation

`cv2.findContours` + `cv2.approxPolyDP`.  Produces piecewise-linear
paths (M/L/Z commands).  Fast, reliable, but produces polygon facets
on curves.  Used as a fast fallback when Bézier quality is not
critical.

### 4b-ii: Catmull-Rom → Cubic Bézier smooth tracing

The higher-quality path.  Full contour points are extracted with
`CHAIN_APPROX_NONE`, then converted to smooth cubic Bézier curves
using the Catmull-Rom spline conversion (see next section).

`cv2.RETR_CCOMP` retrieval mode is used so that holes (inner
contours) are associated with their parent contour — this enables
correct `fill-rule="evenodd"` rendering in SVG.

---

## Bézier Conversion

Given four consecutive contour points P₀, P₁, P₂, P₃, the
Catmull-Rom → cubic Bézier conversion yields control points:

```
CP1 = P₁ + (P₂ − P₀) / 6
CP2 = P₂ − (P₃ − P₁) / 6
```

The resulting SVG `C` command draws a smooth cubic Bézier from P₁ to
P₂.  The conversion is exact for the uniform Catmull-Rom
parameterization (τ = 0.5, uniform knot spacing).

**Subsampling:**  Contours with > 500 points are subsampled uniformly
before Bézier fitting to cap SVG path length and file size.

---

## Background Detection

The heuristic samples pixels along the image border (top, bottom,
left, right edges at uniform intervals).  If the per-channel standard
deviation across all edge samples is < 25, the mean color is declared
the background.

When a background is detected and its color matches the largest
K-means cluster (within ΔR+ΔG+ΔB < 60), that cluster is removed
from path tracing and replaced by a single `<rect>` fill — this
substantially reduces SVG complexity and file size.

If the image has an alpha channel and the four corners are all
transparent, no background rect is emitted.

---

## Overlay Metrics

The overlay comparison renders the SVG back to raster (via
`cairosvg`) at the working resolution, then computes:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| MSE    | mean((orig − rendered)²) | Lower = better. 0 = identical. |
| PSNR   | 10·log₁₀(255² / MSE) dB | Higher = better. >30 dB = good. >40 dB = excellent. |

The overlay PNG shows four panels side-by-side:
1. Original raster
2. SVG rendered to raster
3. Diff heatmap (JET colormap — blue = match, red = divergence)
4. 50/50 blended overlay

---

## Tuning Guide

| Situation | Recommendation |
|-----------|---------------|
| Simple flat logo (< 5 colors) | `--colors 5 --detail low` |
| Detailed logo with gradients  | `--colors 12 --detail high` |
| Logo with fine text            | `--detail high --method potrace` with low turdsize |
| Very noisy source image        | `--detail low` (aggressive morph cleanup) |
| Want smallest SVG file         | `--colors 4 --detail low` |
| Want most accurate SVG         | `--colors 16 --detail high --method potrace` |

**Iterative refinement:**  The skill supports running multiple passes.
If the first result is unsatisfactory, Claude should analyze the
overlay diff and adjust parameters (more/fewer colors, different
detail level) before re-running.
