# Print CSS Reference

Complete, copy-ready CSS and HTML snippets for print-optimized artifacts.

## Table of Contents

1. [Full @media print template](#full-media-print-template)
2. [Print button — HTML version](#print-button--html)
3. [Print button — React version](#print-button--react)
4. [Page break utilities](#page-break-utilities)
5. [Dark theme override](#dark-theme-override)
6. [Table handling](#table-handling)
7. [Image handling](#image-handling)
8. [Expand collapsed content](#expand-collapsed-content)
9. [Link URL display](#link-url-display)
10. [Force background colors](#force-background-colors)
11. [Multi-column print](#multi-column-print)
12. [Header and footer via CSS](#header-and-footer-via-css)

---

## Full @media print template

This is the baseline. Paste it at the end of your `<style>` block.
Adapt selectors to match your artifact's actual class names.

```css
/* ============================================================
   PRINT STYLESHEET
   ============================================================ */

@page {
  size: A4;              /* Change to 'letter' for US */
  margin: 15mm;          /* Comfortable margins; tweak per use case */
}

@media print {

  /* --- RESET LAYOUT TRAPS ----------------------------------- */
  *,
  *::before,
  *::after {
    /* Prevent box-shadow / text-shadow ink waste */
    box-shadow: none !important;
    text-shadow: none !important;
  }

  html, body {
    width: 100% !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    background: #fff !important;
    color: #000 !important;
    font-size: 11pt;          /* Comfortable print body size */
    line-height: 1.45;
  }

  /* --- HIDE UI CHROME --------------------------------------- */
  .no-print,
  .print-button,
  button[onclick*="print"],
  nav,
  .toolbar,
  .sidebar,
  .toast,
  .tooltip,
  .modal-backdrop,
  [role="navigation"],
  [data-no-print] {
    display: none !important;
  }

  /* --- NEUTRALIZE CONTAINERS -------------------------------- */
  /* Any scrollable or height-constrained container must expand  */
  [style*="overflow"],
  [style*="max-height"],
  [class*="scroll"],
  .overflow-auto,
  .overflow-hidden,
  .overflow-y-auto,
  .overflow-x-auto {
    overflow: visible !important;
    max-height: none !important;
    height: auto !important;
  }

  /* --- POSITION RESETS -------------------------------------- */
  /* Fixed/sticky elements overlap on paper */
  .fixed, .sticky,
  [style*="position: fixed"],
  [style*="position: sticky"] {
    position: static !important;
  }

  /* --- VIEWPORT UNITS --------------------------------------- */
  /* vh/vw are meaningless on paper; fall back to auto          */
  [style*="100vh"],
  [style*="100vw"] {
    height: auto !important;
    width: 100% !important;
    min-height: 0 !important;
  }

  /* --- TYPOGRAPHY ------------------------------------------- */
  h1 { font-size: 20pt; }
  h2 { font-size: 16pt; }
  h3 { font-size: 13pt; }
  p, li, td, th, dd, dt { font-size: 11pt; }

  /* Widows & orphans: keep at least 3 lines together          */
  p, li, dd {
    widows: 3;
    orphans: 3;
  }

  /* Never break a heading away from the content after it       */
  h1, h2, h3, h4, h5, h6 {
    break-after: avoid;
    page-break-after: avoid;   /* legacy */
  }

  /* --- PAGE BREAKS ------------------------------------------ */
  /* Avoid breaking inside these logical blocks                 */
  tr, figure, blockquote, pre, code,
  .card, .panel, .section, .item,
  [data-break-avoid] {
    break-inside: avoid;
    page-break-inside: avoid;  /* legacy */
  }

  /* Explicit page break before marked sections                 */
  .page-break, [data-break-before] {
    break-before: page;
    page-break-before: always; /* legacy */
  }

  /* --- IMAGES ----------------------------------------------- */
  img, svg {
    max-width: 100% !important;
    height: auto !important;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  /* --- LINKS ------------------------------------------------ */
  a {
    color: #000 !important;
    text-decoration: underline;
  }

  /* Optionally show URL after external links                   */
  /* Uncomment the block below if you want URLs printed:
  a[href^="http"]::after {
    content: " (" attr(href) ")";
    font-size: 0.8em;
    font-weight: normal;
    word-break: break-all;
  }
  */

  /* --- TABLES ----------------------------------------------- */
  table {
    border-collapse: collapse;
    width: 100%;
  }
  thead {
    display: table-header-group;   /* Repeat headers on each page */
  }
  tfoot {
    display: table-footer-group;
  }
  th, td {
    border: 0.5pt solid #666;
    padding: 4pt 6pt;
  }
}
```

---

## Print button — HTML

Paste this before the closing `</body>` or at the end of your artifact's HTML.

```html
<!-- Print Button -->
<button
  class="print-button"
  onclick="window.print()"
  title="Print this page"
  aria-label="Print"
>
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
       viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
  <span>Print</span>
</button>

<style>
  .print-button {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: none;
    border-radius: 8px;
    background: #1a1a2e;
    color: #fff;
    font-size: 13px;
    font-family: inherit;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
    transition: transform 0.15s ease, opacity 0.15s ease;
  }
  .print-button:hover {
    transform: translateY(-1px);
    opacity: 0.92;
  }
  @media print {
    .print-button { display: none !important; }
  }
</style>
```

### Variations

**Icon-only (compact):**
```html
<button class="print-button" onclick="window.print()" title="Print" aria-label="Print">
  🖨
</button>
<style>
  .print-button {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    width: 40px; height: 40px;
    border: none;
    border-radius: 50%;
    background: #333;
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
    transition: transform 0.15s ease;
  }
  .print-button:hover { transform: scale(1.08); }
  @media print { .print-button { display: none !important; } }
</style>
```

**Integrated in a toolbar:**
```html
<div class="toolbar">
  <!-- ... other toolbar items ... -->
  <button onclick="window.print()" class="toolbar-btn" title="Print">
    🖨 Print
  </button>
</div>
```
Add `.toolbar { display: none !important; }` inside your `@media print` block.

---

## Print button — React

```tsx
function PrintButton({ label = "Print", className = "" }) {
  return (
    <>
      <button
        onClick={() => window.print()}
        className={`print-btn ${className}`}
        title="Print this page"
        aria-label="Print"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"
             viewBox="0 0 24 24" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 6 2 18 2 18 9"/>
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
          <rect x="6" y="14" width="12" height="8"/>
        </svg>
        <span>{label}</span>
      </button>
      <style>{`
        .print-btn {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 9999;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border: none;
          border-radius: 8px;
          background: #1a1a2e;
          color: #fff;
          font-size: 13px;
          font-family: inherit;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(0,0,0,0.18);
          transition: transform 0.15s ease, opacity 0.15s ease;
        }
        .print-btn:hover {
          transform: translateY(-1px);
          opacity: 0.92;
        }
        @media print {
          .print-btn { display: none !important; }
        }
      `}</style>
    </>
  );
}
```

Usage: `<PrintButton />` or `<PrintButton label="Save PDF" />`.

---

## Page break utilities

CSS utility classes you can add to any element:

```css
/* Force a page break BEFORE this element */
.break-before { break-before: page; page-break-before: always; }

/* Force a page break AFTER this element */
.break-after  { break-after: page;  page-break-after: always;  }

/* Prevent a page break INSIDE this element */
.break-avoid  { break-inside: avoid; page-break-inside: avoid; }
```

Apply via `class="break-before"` in HTML, or `data-break-before` attribute
(matched by the `[data-break-before]` selector in the main template).

---

## Dark theme override

If the artifact uses a dark theme on screen, force a light print theme:

```css
@media print {
  :root {
    --bg: #fff !important;
    --text: #000 !important;
    --border: #ccc !important;
    --muted: #666 !important;
    /* Override any other CSS variables from the dark theme */
  }

  body, main, article, section, div {
    background: #fff !important;
    color: #000 !important;
  }

  /* If using Tailwind dark: classes, override them */
  .dark, [data-theme="dark"] {
    background: #fff !important;
    color: #000 !important;
  }
}
```

---

## Table handling

Tables that span multiple pages need repeated headers. The CSS in the main
template already handles this (`thead { display: table-header-group; }`).

For wide tables that risk horizontal overflow:

```css
@media print {
  table {
    font-size: 9pt;       /* Shrink slightly if needed */
    word-break: break-word;
  }
  /* Or rotate the page for this table only */
  .wide-table-page {
    break-before: page;
  }
}
/* Use a landscape @page for a named page: */
@page landscape {
  size: A4 landscape;
}
.wide-table-page {
  page: landscape;
}
```

---

## Image handling

```css
@media print {
  img, svg, canvas {
    max-width: 100% !important;
    height: auto !important;
    break-inside: avoid;
  }
  /* For canvas-based charts, consider rendering a static fallback
     in the beforeprint event:
     window.addEventListener('beforeprint', () => { ... });
  */
}
```

---

## Expand collapsed content

Force `<details>` elements open and hide the toggle:

```css
@media print {
  details {
    display: block !important;
  }
  details > summary {
    display: none !important;
  }
  details[open] > * {
    display: block !important;
  }
}
```

For JS-controlled accordions/tabs, use the `beforeprint` event:

```js
window.addEventListener('beforeprint', () => {
  document.querySelectorAll('.accordion-panel, .tab-panel').forEach(el => {
    el.style.display = 'block';
    el.style.height = 'auto';
    el.style.overflow = 'visible';
  });
});
window.addEventListener('afterprint', () => {
  // Optionally restore collapsed state
});
```

---

## Link URL display

Show the full URL after every external link (useful for reference documents):

```css
@media print {
  a[href^="http"]::after,
  a[href^="//"]::after {
    content: " (" attr(href) ")";
    font-size: 0.8em;
    font-weight: normal;
    font-style: italic;
    color: #555;
    word-break: break-all;
  }
  /* Skip for images-as-links and nav links */
  a[href^="http"] > img { display: inline; }
  nav a[href]::after { content: none !important; }
}
```

---

## Force background colors

By default, browsers strip backgrounds in print. To preserve them on specific
elements (badges, status indicators, colored headers):

```css
@media print {
  .badge,
  .status,
  .colored-header,
  [data-print-bg] {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    color-adjust: exact;
  }
}
```

---

## Multi-column print

For content that benefits from a two-column layout on paper (e.g., glossaries,
reference cards):

```css
@media print {
  .print-columns {
    columns: 2;
    column-gap: 20pt;
    column-rule: 0.5pt solid #ccc;
  }
  .print-columns > * {
    break-inside: avoid;
  }
}
```

---

## Header and footer via CSS

CSS-based running headers/footers have limited browser support. For basic needs:

```css
@page {
  size: A4;
  margin: 20mm 15mm 25mm 15mm;

  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 9pt;
    color: #999;
  }
  @top-right {
    content: "Document Title";
    font-size: 9pt;
    color: #999;
  }
}
```

> **Note:** `@top-*` and `@bottom-*` margin boxes work in Chrome/Edge print
> but are not supported in Firefox or Safari as of 2025. For cross-browser
> page numbering, a JS-based approach with fixed header/footer elements and
> a CSS counter is more reliable but more complex.
