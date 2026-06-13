---
name: print-ready
description: >
  Add print-optimized CSS and a print action button to any HTML or React artifact.
  Use this skill whenever the user asks to "make printable", "add print", "print version",
  "print-friendly", "print CSS", "print button", "export to PDF via print", "print layout",
  "page breaks", "print stylesheet", or any variation of making web content render correctly
  when sent to a printer or saved as PDF via the browser print dialog. Also trigger when the
  user creates an HTML/React artifact and mentions printing, paper, A4, Letter, or PDF export.
  Trigger even for casual phrasing like "I want to print this", "make it printable",
  "add a print button", or "this needs to look good on paper". If the output is an HTML or
  React artifact and printing is mentioned at all, use this skill.
---

# Print-Ready Skill

Transform any HTML or React artifact into a print-optimized document with a single-click
print action. This skill provides a battle-tested print CSS layer and a non-intrusive
print trigger that disappears from the printed output.

## When to apply

- The user explicitly asks for print support, a print button, or print CSS.
- The user is building a document-like artifact (report, invoice, certificate, letter,
  resume, ticket, receipt, schedule, checklist) that will likely be printed.
- The user mentions "PDF export" in the context of browser-based print-to-PDF.

## Core principles

1. **Screen-first, print-enhanced.** The artifact must look great on screen. Print styles
   live entirely inside a `@media print` block and a `@page` rule — they never leak into
   the screen layout.
2. **The print button vanishes.** Any UI chrome (buttons, navbars, tooltips, interactive
   controls) must be hidden via `@media print`. The user sees a clean document on paper.
3. **No content loss.** Overflow, clipping, max-height, and scroll containers must be
   neutralized in print so every piece of content reaches the page.
4. **Controlled page breaks.** Use `break-inside: avoid` on logical units (cards, tables,
   figures, blockquotes). Use `break-before: page` for explicit new-page boundaries.
5. **Ink economy.** Strip decorative backgrounds and shadows in print unless the user
   explicitly wants them (e.g., colored certificates). Ensure text is high-contrast black
   on white by default.

## Implementation — HTML artifacts

Read `references/print-css.md` before writing any code. It contains the full annotated
CSS template, the print-button component, and edge-case handling.

### Minimal integration checklist

1. **Add the print button.** Place a fixed-position button (bottom-right corner, `z-index: 9999`)
   that calls `window.print()`. Style it to be visible on screen, hidden in print.

2. **Inject the `@media print` block.** Either inline in a `<style>` tag or at the end of
   your existing `<style>`. The reference file has the full template — copy the relevant
   sections.

3. **Set `@page` rules.** Default to `@page { size: A4; margin: 15mm; }` unless the user
   specifies Letter or another size.

4. **Neutralize interactive/scrollable containers.** Any element with `overflow: auto/hidden/scroll`,
   `max-height`, or `height` constraints must become `overflow: visible; max-height: none; height: auto`
   inside `@media print`.

5. **Expand collapsed content.** Accordions, tabs, `<details>` elements — force them open
   in print via `details[open] { display: block; }` and `details > summary { display: none; }` patterns,
   or by toggling state in the `beforeprint` event.

6. **Handle links.** Optionally append the URL after link text:
   `a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.8em; }`.
   Skip this for purely decorative or navigation links.

7. **Force background printing where needed.** For elements that MUST keep their background
   (e.g., colored badges, status indicators), use:
   `-webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact;`.

## Implementation — React artifacts (.jsx)

The same CSS applies. Differences:

- The print button is a React component. Use `onClick={() => window.print()}`.
- If using Tailwind, add the print styles via a `<style>` tag injected inside the component's
  return, or via `@media print` in a `<style jsx>` / inline style block. Do NOT rely on
  Tailwind's `print:` variant alone — it lacks `@page` control and advanced break rules.
- Place the `<style>` block at the top of the component's JSX return so it's always mounted.

## Print button design

The default print button is a small, tasteful floating action button. It should feel native
to the artifact's design language — not a bolted-on afterthought.

```
Positioning:  fixed, bottom: 20px, right: 20px
Size:         40×40px (icon) or auto-width with label
Shape:        rounded (border-radius: 8px or circular)
Icon:         Printer SVG or the text "Print" / "🖨"
Colors:       Match the artifact's palette; neutral fallback: #333 bg, #fff text
Hover:        Subtle scale or opacity shift
Print media:  display: none !important
```

If the artifact already has a toolbar or action bar, integrate the print trigger there
instead of adding a floating button.

## Page size reference

| Name    | CSS `size` value   | Dimensions         |
|---------|--------------------|---------------------|
| A4      | `A4`               | 210 × 297 mm       |
| Letter  | `letter`           | 8.5 × 11 in        |
| Legal   | `legal`            | 8.5 × 14 in        |
| A3      | `A3`               | 297 × 420 mm       |

Default to **A4** unless the user specifies otherwise or their locale suggests Letter
(US-based users).

## Common pitfalls

- **Flexbox/Grid gaps vanish across page breaks.** Wrap flex/grid children in a block-level
  container and apply `break-inside: avoid` to the container.
- **`position: fixed/sticky` elements overlap content.** Reset to `position: static` in print.
- **`vh`/`vw` units produce bizarre sizing on paper.** Replace with `auto`, `100%`, or
  absolute units in print.
- **Web fonts may not embed in PDF.** Use `@media print { font-family: serif; }` as a
  fallback if font embedding matters.
- **Dark themes produce ink-heavy prints.** Always override to light background + dark text
  in `@media print` unless the user explicitly opts out.

## Validation

After adding print support, mentally walk through:

1. Does `Ctrl+P` / `Cmd+P` show a clean preview with no UI chrome?
2. Are page breaks in sensible places (not splitting a heading from its paragraph)?
3. Is all content visible (nothing cut off by overflow or max-height)?
4. Is the print button invisible in the preview?
5. Are backgrounds stripped (or explicitly preserved where needed)?
