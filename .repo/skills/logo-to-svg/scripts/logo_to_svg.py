#!/usr/bin/env python3
"""
logo_to_svg.py — Raster logo → SVG vector conversion pipeline.

Pipeline stages:
  1. Load & preprocess (denoise, resize, alpha handling)
  2. Color quantization via K-means clustering
  3. Per-color-layer binary mask extraction
  4. Bitmap → vector tracing (potrace preferred, OpenCV fallback)
  5. SVG assembly with proper viewBox, colors, and layering
  6. Overlay verification (raster diff between original and rendered SVG)

Usage:
  python3 logo_to_svg.py INPUT_IMAGE [--output OUTPUT.svg] [--colors N]
                          [--tolerance T] [--detail LEVEL] [--script-copy PATH]

Dependencies (pip install --break-system-packages):
  - opencv-python (cv2)
  - numpy
  - Pillow
  - scikit-learn
  - svgwrite
  - cairosvg
  System: potrace (apt install potrace)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

# Optional — graceful fallback if missing
try:
    import svgwrite
    HAS_SVGWRITE = True
except ImportError:
    HAS_SVGWRITE = False

try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False

POTRACE_BIN = shutil.which("potrace")

# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────
@dataclass
class ColorLayer:
    """One color plane extracted from the quantized image."""
    index: int
    rgb: tuple[int, int, int]
    hex: str
    mask: np.ndarray          # uint8 binary mask (0 or 255)
    pixel_ratio: float        # fraction of non-transparent pixels
    svg_paths: list[str] = field(default_factory=list)
    potrace_transform: Optional[str] = None  # transform from potrace output


@dataclass
class ConversionResult:
    """Full result bundle returned by the pipeline."""
    svg_text: str
    svg_path: str
    script_path: Optional[str]
    overlay_path: Optional[str]
    colors_used: list[dict]
    width: int
    height: int
    method: str               # "potrace" | "opencv"
    stats: dict = field(default_factory=dict)


# ─────────────────────────────────────────────
# 1. Preprocessing
# ─────────────────────────────────────────────
def load_and_preprocess(
    path: str,
    max_dim: int = 2000,
    denoise_strength: int = 5,
) -> tuple[np.ndarray, np.ndarray | None, int, int]:
    """
    Load image, handle alpha, resize if needed, denoise.
    Returns (bgr_image, alpha_channel_or_None, orig_w, orig_h).
    """
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")

    orig_h, orig_w = img.shape[:2]
    alpha = None

    # Extract alpha if present (4-channel)
    if img.ndim == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        img = img[:, :, :3]
    elif img.ndim == 2:
        # Grayscale → BGR
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Resize large images (preserve aspect ratio)
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        if alpha is not None:
            alpha = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Light denoise (preserve edges)
    if denoise_strength > 0:
        img = cv2.fastNlMeansDenoisingColored(
            img, None, denoise_strength, denoise_strength, 7, 21
        )

    return img, alpha, orig_w, orig_h


# ─────────────────────────────────────────────
# 2. Color quantization
# ─────────────────────────────────────────────
def quantize_colors(
    img: np.ndarray,
    alpha: np.ndarray | None,
    n_colors: int = 8,
    min_pixel_ratio: float = 0.005,
) -> tuple[list[ColorLayer], np.ndarray]:
    """
    K-means color quantization.  Returns color layers sorted by area
    (largest first) and the quantized BGR image.

    Pixels where alpha < 128 are excluded from clustering and assigned
    to a transparent layer (not returned).
    """
    h, w = img.shape[:2]

    # Build sample mask (opaque pixels only)
    if alpha is not None:
        opaque_mask = alpha >= 128
    else:
        opaque_mask = np.ones((h, w), dtype=bool)

    pixels = img[opaque_mask].reshape(-1, 3).astype(np.float32)
    n_opaque = pixels.shape[0]

    if n_opaque == 0:
        raise ValueError("Image is fully transparent — nothing to vectorize.")

    # Clamp n_colors to actual unique colors
    unique = np.unique(pixels, axis=0)
    effective_k = min(n_colors, len(unique))

    km = KMeans(n_clusters=effective_k, n_init=10, random_state=42)
    labels_flat = km.fit_predict(pixels)
    centers = km.cluster_centers_.astype(np.uint8)

    # Rebuild full-image label map (-1 = transparent)
    label_map = np.full((h, w), -1, dtype=np.int32)
    label_map[opaque_mask] = labels_flat

    # Build quantized image
    quantized = img.copy()
    for i, center in enumerate(centers):
        quantized[label_map == i] = center

    # Build layers
    layers: list[ColorLayer] = []
    for i, center in enumerate(centers):
        mask = ((label_map == i).astype(np.uint8)) * 255
        ratio = np.count_nonzero(mask) / max(n_opaque, 1)
        if ratio < min_pixel_ratio:
            continue
        b, g, r = int(center[0]), int(center[1]), int(center[2])
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        layers.append(ColorLayer(
            index=i, rgb=(r, g, b), hex=hex_color,
            mask=mask, pixel_ratio=ratio,
        ))

    layers.sort(key=lambda l: l.pixel_ratio, reverse=True)
    return layers, quantized


# ─────────────────────────────────────────────
# 3. Mask refinement
# ─────────────────────────────────────────────
def refine_mask(mask: np.ndarray, detail: str = "medium") -> np.ndarray:
    """
    Morphological cleanup of a binary mask.
    detail: "low" (aggressive smoothing) | "medium" | "high" (preserve fine detail)
    """
    kernel_sizes = {"low": 5, "medium": 3, "high": 1}
    ks = kernel_sizes.get(detail, 3)

    if ks <= 1:
        return mask

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    # Close small gaps, then open to remove noise
    refined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, kernel, iterations=1)
    return refined


# ─────────────────────────────────────────────
# 4a. Vectorization — potrace path
# ─────────────────────────────────────────────
def trace_with_potrace(
    mask: np.ndarray,
    turdsize: int = 2,
    alphamax: float = 1.0,
    opttolerance: float = 0.2,
) -> tuple[list[str], Optional[str]]:
    """
    Use the potrace binary to convert a binary mask to SVG path strings.
    Returns (list_of_path_d_strings, transform_string_or_None).

    Potrace outputs paths in a scaled, y-flipped coordinate system with a
    <g transform="translate(0,H) scale(0.1,-0.1)"> wrapper.  We extract
    both the paths and the transform so the SVG assembler can apply it.
    """
    if POTRACE_BIN is None:
        return [], None

    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp_bmp:
        bmp_path = tmp_bmp.name
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp_svg:
        svg_path = tmp_svg.name

    try:
        # potrace expects a PBM/BMP with black = foreground
        # Our mask: 255 = foreground, so invert for potrace (black = ink)
        pil_mask = Image.fromarray(255 - mask)
        pil_mask.save(bmp_path)

        cmd = [
            POTRACE_BIN,
            bmp_path,
            "-s",                           # SVG output
            "-o", svg_path,
            "-t", str(turdsize),            # suppress speckles
            "-a", str(alphamax),            # corner threshold
            "-O", str(opttolerance),        # curve optimization
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)

        svg_text = Path(svg_path).read_text()

        # Extract the transform from <g transform="...">
        transform_match = re.search(
            r'<g\s+transform="([^"]+)"', svg_text
        )
        transform = transform_match.group(1) if transform_match else None

        # Extract all d="..." from <path> elements
        paths = re.findall(r'<path[^>]*\bd="([^"]+)"', svg_text)
        return paths, transform

    except Exception:
        return [], None
    finally:
        for p in (bmp_path, svg_path):
            try:
                os.unlink(p)
            except OSError:
                pass


# ─────────────────────────────────────────────
# 4b. Vectorization — OpenCV contour fallback
# ─────────────────────────────────────────────
def trace_with_opencv(
    mask: np.ndarray,
    epsilon_factor: float = 0.001,
    min_area: int = 10,
) -> list[str]:
    """
    Extract contours with cv2.findContours, approximate with Douglas-Peucker,
    and convert to SVG path data strings.
    """
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS,
    )
    if not contours:
        return []

    h, w = mask.shape[:2]
    perimeter_ref = 2 * (h + w)
    epsilon = epsilon_factor * perimeter_ref

    paths: list[str] = []
    for i, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < min_area:
            continue

        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if len(approx) < 3:
            continue

        pts = approx.reshape(-1, 2)
        d_parts = [f"M {pts[0][0]},{pts[0][1]}"]
        for pt in pts[1:]:
            d_parts.append(f"L {pt[0]},{pt[1]}")
        d_parts.append("Z")

        paths.append(" ".join(d_parts))

    return paths


def trace_with_opencv_bezier(
    mask: np.ndarray,
    min_area: int = 10,
) -> list[str]:
    """
    Higher-quality OpenCV tracing using cubic Bézier approximation
    of contour points for smoother curves.
    """
    contours, hierarchy = cv2.findContours(
        mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE,
    )
    if not contours:
        return []

    paths: list[str] = []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue

        pts = cnt.reshape(-1, 2).astype(float)
        n = len(pts)
        if n < 4:
            # Too few points for bezier, use line segments
            d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"
            for p in pts[1:]:
                d += f" L {p[0]:.1f},{p[1]:.1f}"
            d += " Z"
            paths.append(d)
            continue

        # Subsample if too many points (performance)
        if n > 500:
            step = max(1, n // 500)
            pts = pts[::step]
            n = len(pts)

        # Build cubic bezier path using Catmull-Rom → cubic Bezier conversion
        d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(n):
            p0 = pts[(i - 1) % n]
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n]

            # Catmull-Rom to cubic Bezier control points
            cp1x = p1[0] + (p2[0] - p0[0]) / 6.0
            cp1y = p1[1] + (p2[1] - p0[1]) / 6.0
            cp2x = p2[0] - (p3[0] - p1[0]) / 6.0
            cp2y = p2[1] - (p3[1] - p1[1]) / 6.0

            d += f" C {cp1x:.1f},{cp1y:.1f} {cp2x:.1f},{cp2y:.1f} {p2[0]:.1f},{p2[1]:.1f}"

        d += " Z"
        paths.append(d)

    return paths


# ─────────────────────────────────────────────
# 5. SVG assembly
# ─────────────────────────────────────────────
def assemble_svg(
    layers: list[ColorLayer],
    width: int,
    height: int,
    background: Optional[str] = None,
) -> str:
    """
    Build a complete SVG document from traced color layers.
    Layers are rendered back-to-front (largest area first = background).

    Potrace-traced layers are wrapped in a <g> with the potrace transform
    (typically translate + scale to handle y-flip and 10x scaling).
    OpenCV-traced layers use raw pixel coordinates (no transform needed).
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
    ]

    if background:
        lines.append(
            f'  <rect width="{width}" height="{height}" fill="{background}"/>'
        )

    for layer in layers:
        if not layer.svg_paths:
            continue
        hex_c = layer.hex
        combined_d = " ".join(layer.svg_paths)

        if layer.potrace_transform:
            # Wrap in <g> with potrace's coordinate transform
            lines.append(
                f'  <g transform="{layer.potrace_transform}">'
            )
            lines.append(
                f'    <path d="{combined_d}" '
                f'fill="{hex_c}" fill-rule="evenodd" stroke="none"/>'
            )
            lines.append('  </g>')
        else:
            # OpenCV paths are already in image pixel coordinates
            lines.append(
                f'  <path d="{combined_d}" '
                f'fill="{hex_c}" fill-rule="evenodd" stroke="none"/>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# 6. Overlay verification
# ─────────────────────────────────────────────
def render_svg_to_raster(svg_text: str, width: int, height: int) -> np.ndarray | None:
    """Render SVG to a BGR numpy array via cairosvg."""
    if not HAS_CAIROSVG:
        return None

    try:
        png_data = cairosvg.svg2png(
            bytestring=svg_text.encode("utf-8"),
            output_width=width,
            output_height=height,
        )
        arr = np.frombuffer(png_data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
        # Convert BGRA → BGR if needed
        if img.ndim == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img
    except Exception:
        return None


def create_overlay_comparison(
    original: np.ndarray,
    svg_text: str,
    output_path: str,
) -> Optional[str]:
    """
    Render the SVG, produce a side-by-side + diff overlay image.
    Returns path to overlay PNG or None on failure.
    """
    h, w = original.shape[:2]
    rendered = render_svg_to_raster(svg_text, w, h)
    if rendered is None:
        return None

    # Resize rendered to match original exactly
    rendered = cv2.resize(rendered, (w, h), interpolation=cv2.INTER_AREA)

    # Compute absolute difference
    diff = cv2.absdiff(original, rendered)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # Amplify diff for visibility
    diff_amplified = cv2.applyColorMap(
        cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
        cv2.COLORMAP_JET,
    )

    # Blended overlay (50/50 original + SVG render)
    blended = cv2.addWeighted(original, 0.5, rendered, 0.5, 0)

    # Compose: [Original | SVG Render | Diff Heatmap | Blended]
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    label_h = 30
    panels = []
    for img, label in [
        (original, "Original"),
        (rendered, "SVG Render"),
        (diff_amplified, "Diff Heatmap"),
        (blended, "Overlay 50/50"),
    ]:
        panel = np.zeros((h + label_h, w, 3), dtype=np.uint8)
        panel[label_h:, :] = img
        cv2.putText(panel, label, (5, 20), font, 0.6, (255, 255, 255), 1)
        panels.append(panel)

    composite = np.hstack(panels)
    cv2.imwrite(output_path, composite)

    # Compute similarity metrics
    mse = np.mean(diff_gray.astype(float) ** 2)
    psnr = 10 * math.log10(255**2 / max(mse, 1e-10)) if mse > 0 else float("inf")

    return output_path, {"mse": round(mse, 2), "psnr_db": round(psnr, 2)}


# ─────────────────────────────────────────────
# 7. Background detection
# ─────────────────────────────────────────────
def detect_background_color(
    img: np.ndarray,
    alpha: np.ndarray | None,
) -> Optional[str]:
    """
    Heuristic: sample the four corners + edge pixels.
    If they converge on a single color, that is the background.
    Returns hex string or None (transparent background).
    """
    if alpha is not None:
        # If corners are transparent, background is transparent
        h, w = alpha.shape
        corners = [alpha[0, 0], alpha[0, w-1], alpha[h-1, 0], alpha[h-1, w-1]]
        if all(c < 128 for c in corners):
            return None

    h, w = img.shape[:2]
    margin = max(1, min(h, w) // 20)
    samples = []
    # Top edge
    samples.extend(img[0, ::max(1, w//20)].tolist())
    # Bottom edge
    samples.extend(img[h-1, ::max(1, w//20)].tolist())
    # Left edge
    samples.extend(img[::max(1, h//20), 0].tolist())
    # Right edge
    samples.extend(img[::max(1, h//20), w-1].tolist())

    samples = np.array(samples, dtype=np.float32)
    mean = samples.mean(axis=0)
    std = samples.std(axis=0).mean()

    # If edge pixels are consistent (low std), that's the background
    if std < 25:
        b, g, r = int(mean[0]), int(mean[1]), int(mean[2])
        return f"#{r:02x}{g:02x}{b:02x}"
    return None


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────
def convert_logo(
    input_path: str,
    output_path: str = "logo.svg",
    n_colors: int = 8,
    detail: str = "medium",
    tolerance: float = 0.001,
    max_dim: int = 2000,
    force_method: Optional[str] = None,
    script_copy_path: Optional[str] = None,
    overlay_path: Optional[str] = None,
) -> ConversionResult:
    """
    Full pipeline: raster logo → SVG vector.

    Parameters:
      input_path:       Path to input image (PNG, JPG, BMP, etc.)
      output_path:      Where to write the SVG
      n_colors:         Max colors for K-means quantization
      detail:           "low" | "medium" | "high" — morphological cleanup level
      tolerance:        Douglas-Peucker epsilon factor (lower = more detail)
      max_dim:          Resize images larger than this
      force_method:     "potrace" | "opencv" | None (auto-select)
      script_copy_path: If set, copy this script to that path
      overlay_path:     If set, write overlay comparison PNG here
    """
    print(f"[1/6] Loading and preprocessing: {input_path}")
    img, alpha, orig_w, orig_h = load_and_preprocess(input_path, max_dim=max_dim)
    h, w = img.shape[:2]

    print(f"       Image size: {orig_w}x{orig_h} → working at {w}x{h}")

    print(f"[2/6] Detecting background...")
    bg_color = detect_background_color(img, alpha)
    if bg_color:
        print(f"       Background detected: {bg_color}")
    else:
        print(f"       Background: transparent")

    print(f"[3/6] Color quantization (K={n_colors})...")
    layers, quantized = quantize_colors(img, alpha, n_colors=n_colors)
    print(f"       Found {len(layers)} significant color layers:")
    for l in layers:
        print(f"         {l.hex} — {l.pixel_ratio*100:.1f}% of pixels")

    # Decide whether to skip the background-color layer in the SVG
    # (if bg_color matches the largest layer, we use a rect instead)
    bg_layer_idx = None
    if bg_color and layers:
        # Check if largest layer is close to detected background
        lr, lg, lb = layers[0].rgb
        br = int(bg_color[1:3], 16)
        bg_g = int(bg_color[3:5], 16)
        bb = int(bg_color[5:7], 16)
        if abs(lr - br) + abs(lg - bg_g) + abs(lb - bb) < 60:
            bg_layer_idx = 0

    print(f"[4/6] Refining masks (detail={detail})...")
    for layer in layers:
        layer.mask = refine_mask(layer.mask, detail=detail)

    # Select tracing method
    method = force_method
    if method is None:
        method = "potrace" if POTRACE_BIN else "opencv"

    print(f"[5/6] Vectorizing with {method}...")

    potrace_params = {
        "low": {"turdsize": 5, "alphamax": 1.5, "opttolerance": 0.5},
        "medium": {"turdsize": 2, "alphamax": 1.0, "opttolerance": 0.2},
        "high": {"turdsize": 0, "alphamax": 0.6, "opttolerance": 0.1},
    }
    pp = potrace_params.get(detail, potrace_params["medium"])

    for i, layer in enumerate(layers):
        if bg_layer_idx is not None and i == bg_layer_idx:
            # Skip tracing background — will use <rect> instead
            continue

        if method == "potrace":
            paths, transform = trace_with_potrace(layer.mask, **pp)
            if paths:
                layer.potrace_transform = transform
            else:
                # Fallback to OpenCV bezier if potrace fails
                paths = trace_with_opencv_bezier(layer.mask, min_area=10)
        else:
            paths = trace_with_opencv_bezier(layer.mask, min_area=10)

        layer.svg_paths = paths
        print(f"         Layer {layer.hex}: {len(paths)} paths")

    # Remove background layer from SVG layers if using rect
    svg_layers = layers
    svg_bg = None
    if bg_layer_idx is not None:
        svg_bg = layers[bg_layer_idx].hex
        svg_layers = [l for i, l in enumerate(layers) if i != bg_layer_idx]

    print(f"[6/6] Assembling SVG...")
    svg_text = assemble_svg(svg_layers, w, h, background=svg_bg)

    # Write SVG
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(svg_text, encoding="utf-8")
    print(f"       Written: {output_path}")

    # Overlay comparison
    overlay_result = None
    stats = {}
    if overlay_path:
        print(f"       Generating overlay comparison...")
        result = create_overlay_comparison(img, svg_text, overlay_path)
        if result:
            overlay_result, metrics = result
            stats.update(metrics)
            print(f"       Overlay: {overlay_path}")
            print(f"       MSE={metrics['mse']}, PSNR={metrics['psnr_db']}dB")

    # Copy script if requested
    actual_script_path = None
    if script_copy_path:
        src = Path(__file__)
        dst = Path(script_copy_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        actual_script_path = str(dst)
        print(f"       Script copied to: {actual_script_path}")

    colors_info = [
        {"hex": l.hex, "rgb": l.rgb, "pixel_ratio": round(l.pixel_ratio, 4),
         "path_count": len(l.svg_paths)}
        for l in layers
    ]

    return ConversionResult(
        svg_text=svg_text,
        svg_path=output_path,
        script_path=actual_script_path,
        overlay_path=overlay_result,
        colors_used=colors_info,
        width=w, height=h,
        method=method,
        stats=stats,
    )


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Convert a raster logo image to an SVG vector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python3 logo_to_svg.py logo.png
          python3 logo_to_svg.py logo.png --colors 6 --detail high
          python3 logo_to_svg.py logo.png -o out.svg --overlay comparison.png
        """),
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", default=None, help="Output SVG path")
    parser.add_argument("--colors", type=int, default=8,
                        help="Max colors for quantization (default: 8)")
    parser.add_argument("--detail", choices=["low", "medium", "high"],
                        default="medium", help="Detail level (default: medium)")
    parser.add_argument("--tolerance", type=float, default=0.001,
                        help="Curve tolerance (lower = more detail)")
    parser.add_argument("--max-dim", type=int, default=2000,
                        help="Max image dimension (default: 2000)")
    parser.add_argument("--method", choices=["potrace", "opencv"],
                        default=None, help="Force tracing method")
    parser.add_argument("--script-copy", default=None,
                        help="Copy this script to the given path")
    parser.add_argument("--overlay", default=None,
                        help="Write overlay comparison PNG to this path")

    args = parser.parse_args()

    if args.output is None:
        stem = Path(args.input).stem
        args.output = f"{stem}.svg"

    result = convert_logo(
        input_path=args.input,
        output_path=args.output,
        n_colors=args.colors,
        detail=args.detail,
        tolerance=args.tolerance,
        max_dim=args.max_dim,
        force_method=args.method,
        script_copy_path=args.script_copy,
        overlay_path=args.overlay,
    )

    print("\n=== Conversion Summary ===")
    print(f"  Method:     {result.method}")
    print(f"  Dimensions: {result.width}×{result.height}")
    print(f"  Colors:     {len(result.colors_used)}")
    print(f"  SVG:        {result.svg_path}")
    if result.script_path:
        print(f"  Script:     {result.script_path}")
    if result.overlay_path:
        print(f"  Overlay:    {result.overlay_path}")
    if result.stats:
        print(f"  PSNR:       {result.stats.get('psnr_db', 'N/A')} dB")


if __name__ == "__main__":
    main()
