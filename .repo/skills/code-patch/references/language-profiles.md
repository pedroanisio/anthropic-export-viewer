---
title: Language Profiles — code-patch
---

# Language Profiles

How each language's symbols are detected, how IDs are formed, and what
operations are supported.

---

## Symbol ID format

```
<bare_name>               # unambiguous only — fails if duplicate exists
<qualified_name>          # "ClassName.method_name", "ImplName.fn_name"
<kind>:<name>             # type-qualified: "function:foo", "class:Bar"
```

**Kind shorthands accepted:** `fn` → `function`, `func` → `function`,
`cls` → `class`.

**When to use type-qualified IDs:** whenever a file contains both a class
and a function (or struct and fn) with the same name.

---

## Python

| Aspect | Details |
|---|---|
| Symbol kinds | `function`, `class`, `method` |
| Body boundary | Indentation-based |
| Decorator prefix | `@decorator` lines above `def`/`class` are included in symbol extent |
| Comment markers | `# BLOCK:name` / `# END BLOCK:name` / `# ANCHOR:name` |
| Import style | `import x`, `from x import y` |

**Symbol examples:**
```python
def compute(x):          # symbol_id: "compute" or "function:compute"
    return x * 2

class MyService:         # symbol_id: "MyService" or "class:MyService"
    def run(self):       # symbol_id: "MyService.run" or "method:run"
        pass

@cache                   # prefix is part of the symbol extent
def cached_fn():
    pass
```

**Import insert point:** after the last existing import, or before the
first non-comment, non-docstring line.

---

## JavaScript

| Aspect | Details |
|---|---|
| Symbol kinds | `function`, `class`, `method` |
| Body boundary | Brace-counting with string-state tracking |
| Comment markers | `// BLOCK:name` / `// END BLOCK:name` / `// ANCHOR:name` |
| Import style | `import x from 'y'`, `const x = require('y')` |

**Detected patterns:**
```javascript
function add(a, b) { }                    // "function:add"
class Calculator { }                      // "class:Calculator"
const square = (n) => { return n * n; }  // "function:square"
const double = function(n) { return n; } // "function:double"
// Inside a class:
    multiply(x) { }                       // "function:multiply" or "method:multiply"
```

**Caveats:** Template literals and string literals with `{`/`}` are
excluded from brace counting via the string-state tracker. Arrow
functions without a body block (`const f = x => x`) are **not detected
as symbols** — use `edit_text` without a `symbol_id` scope to target
them. Arrow functions **with** a brace body (`const f = (x) => { ... }`)
are fully supported.

---

## TypeScript

Extends the JavaScript profile. Additional symbol kinds:

| Kind | Example |
|---|---|
| `interface` | `interface User { }` → `"interface:User"` |
| `type` | `type Status = ...` → `"type:Status"` |
| `enum` | `enum Direction { }` → `"enum:Direction"` |

All JavaScript patterns are also supported. `import type` statements are
detected as imports.

---

## Rust

| Aspect | Details |
|---|---|
| Symbol kinds | `function`, `struct`, `enum`, `trait`, `impl`, `mod`, `method` |
| Body boundary | Brace-counting (no template literals — safe) |
| Attribute prefix | `#[derive(...)]`, `#[cfg(...)]` etc. above symbols are included |
| Comment markers | `// BLOCK:name` / `// END BLOCK:name` / `// ANCHOR:name` |
| Import style | `use x::y;` |

**Symbol examples:**
```rust
fn add(a: i32, b: i32) -> i32 { }   // "function:add"
struct Point { }                      // "struct:Point"
enum Color { }                        // "enum:Color"
trait Shape { }                       // "trait:Shape"
impl Shape for Point { }              // "impl:Point"
    fn area(&self) -> f64 { }        //   → qualified: "Point.area", kind: "method"
pub mod utils { }                     // "mod:utils"
```

**Method qualification:** functions inside an `impl` block are qualified
as `ImplName.fn_name` and given kind `method`.

**Semicolon-terminated mods** (`mod foo;`) have an empty body extent.

---

## HTML

| Aspect | Details |
|---|---|
| Symbol kinds | `tag` |
| Detection | Tags with `id` attribute, or semantic tags: `section`, `nav`, `header`, `footer`, `main`, `article`, `aside`, `form`, `table`, `figure` |
| Body boundary | Tag-balancing (matching `</tag>`) |
| Comment markers | `<!-- BLOCK:name -->` / `<!-- END BLOCK:name -->` / `<!-- ANCHOR:name -->` |
| Import style | `<link rel="stylesheet">`, `<script src="...">` |

**Symbol examples:**
```html
<div id="hero">...</div>          <!-- "hero" or "tag:hero" -->
<header id="site-header">...</header>  <!-- "site-header" -->
<section>...</section>             <!-- "section" (first one) -->
<nav>...</nav>                     <!-- "nav" -->
```

**Multiple semantic tags:** disambiguated as `section_0`, `section_1`, etc.
Self-closing tags have an empty body.

**`rename_symbol` on HTML:** renames the `id` attribute value in the
opening tag.

---

## CSS

| Aspect | Details |
|---|---|
| Symbol kinds | `rule` |
| Detection | Selectors before `{`, `@media`, `@keyframes`, `@import`, other `@`-rules |
| Body boundary | Brace-counting |
| Comment markers | `/* BLOCK:name */` / `/* END BLOCK:name */` / `/* ANCHOR:name */` |
| Import style | `@import url(...)` |

**Symbol examples:**
```css
.hero { }                    /* "rule:.hero" */
h1 { }                       /* "rule:h1" */
@media (max-width: 768px) { }  /* "rule:@media (max-width: 768px)" */
@keyframes spin { }          /* "rule:@keyframes spin" */
@import url('base.css');     /* detected as import */
```

**`rename_symbol` on CSS:** replaces the selector string in the
declaration line only — it does NOT propagate to other rules that
use the same selector (e.g. inside `@media` blocks). To rename a
selector globally, use `edit_text` without a `symbol_id` scope.

---

## Operation × language matrix

| Operation | Python | JS | TS | Rust | HTML | CSS |
|---|---|---|---|---|---|---|
| `assert` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `rename_symbol` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `replace_symbol` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `delete_symbol` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `move_symbol` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `swap_symbols` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `edit_text` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `replace_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `delete_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `insert_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `move_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `copy_block` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `inject_markers` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `add_import` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `remove_import` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `change_signature` | ✓ | ✓ | ✓ | ✓ | — | — |
| `add_decorator` | ✓ | — | — | ✓ | — | — |
