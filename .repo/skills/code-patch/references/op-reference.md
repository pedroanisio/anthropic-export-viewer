---
title: Operation Reference — code-patch
---

# Operation Reference

All operations are applied in array order. Each op is an object with an
`"op"` field. Symbol IDs are resolved per language profile — see
`language-profiles.md`.

---

## Cross-language operations

### `assert`

Verify that text or a symbol exists in the original file before applying
any mutations. Failure in `atomic` mode returns `STATUS: blocked`.

```json
{
  "op": "assert",
  "contains": "def verify_token",
  "symbol_id": "function:verify_token"  // optional — scope to this symbol
}
```

| Field | Required | Description |
|---|---|---|
| `contains` | yes | Text that must exist in scope |
| `symbol_id` | no | Scope the check to this symbol's body |

---

### `rename_symbol`

Rename a symbol's declaration. Does not update call sites.

```json
{
  "op": "rename_symbol",
  "symbol_id": "function:verify_token",
  "new_name": "validate_token"
}
```

---

### `replace_symbol`

Replace a symbol's entire body (everything between the declaration and the
closing delimiter). The signature/declaration is preserved.

```json
{
  "op": "replace_symbol",
  "symbol_id": "function:compute",
  "new_body": "    return x ** 2\n"
}
```

---

### `delete_symbol`

Remove a symbol entirely, including decorators/attributes in its prefix.

```json
{
  "op": "delete_symbol",
  "symbol_id": "function:deprecated_fn"
}
```

---

### `move_symbol`

Move a symbol to appear after another symbol.

```json
{
  "op": "move_symbol",
  "symbol_id": "function:helper",
  "to_after": "class:MyService"
}
```

---

### `swap_symbols`

Swap the positions of two symbols.

```json
{
  "op": "swap_symbols",
  "symbol_a": "function:foo",
  "symbol_b": "function:bar"
}
```

---

### `edit_text`

Find and replace text, optionally scoped to a symbol.
3-tier matching: exact → whitespace-normalized → fuzzy (if `allow_fuzzy`).

```json
{
  "op": "edit_text",
  "symbol_id": "function:compute",
  "find": "return x * 2",
  "replace": "return x * 3",
  "allow_fuzzy": false
}
```

| Field | Required | Description |
|---|---|---|
| `find` | yes | Text to find |
| `replace` | yes | Replacement text |
| `symbol_id` | no | Scope to this symbol's body |
| `allow_fuzzy` | no | Enable fuzzy (word-overlap) matching tier 3 |

---

### `replace_block`

Replace a named `BLOCK:name` … `END BLOCK:name` marker region, or a text
match.

```json
{
  "op": "replace_block",
  "symbol_id": "function:render",
  "target": "// BLOCK:template",
  "new_content": "const html = `<div>${data}</div>`;"
}
```

---

### `delete_block`

Delete a named block or text match (alias for `replace_block` with empty
`new_content`).

```json
{
  "op": "delete_block",
  "target": "# BLOCK:debug"
}
```

---

### `insert_block`

Insert content after an `ANCHOR:name` marker or after a text match.

```json
{
  "op": "insert_block",
  "symbol_id": "class:MyService",
  "after_anchor": "after_init",
  "new_content": "    self.cache = {}"
}
```

| Field | Required | Description |
|---|---|---|
| `after_anchor` | yes | Anchor name or text to insert after |
| `new_content` | yes | Lines to insert |
| `symbol_id` | no | Scope the anchor search |

---

### `move_block`

Extract a block and insert it elsewhere in the file.

```json
{
  "op": "move_block",
  "source_symbol_id": "function:old_home",
  "source_target": "// BLOCK:logic",
  "target_symbol_id": "function:new_home",
  "after_anchor": "// ANCHOR:insert_here"
}
```

---

### `copy_block`

Copy a block to another location (source is not removed).

```json
{
  "op": "copy_block",
  "source_target": "# BLOCK:shared",
  "after_anchor": "after_imports"
}
```

---

### `inject_markers`

Add `BLOCK` or `ANCHOR` comment markers to the file to enable future
targeted edits.

```json
{
  "op": "inject_markers",
  "symbol_id": "function:render",
  "markers": [
    {
      "type": "block",
      "name": "template",
      "wraps": "const html =",
      "wraps_end": "return html;"
    },
    {
      "type": "anchor",
      "name": "before_return",
      "after": "return html;"
    }
  ]
}
```

Marker types:
- `block` — wraps a region with `BLOCK:name` / `END BLOCK:name`
- `anchor` — inserts `ANCHOR:name` after the matched line

---

## Language-specific operations

### `add_import`

Add an import statement. Skipped with a warning if the statement already
exists (deduplication).

```json
{ "op": "add_import", "statement": "from datetime import timezone" }
{ "op": "add_import", "statement": "import util from 'util';" }
{ "op": "add_import", "statement": "use std::fmt;" }
{ "op": "add_import", "statement": "@import url('theme.css');" }
```

---

### `remove_import`

Remove an existing import statement.

```json
{ "op": "remove_import", "statement": "import os" }
{ "op": "remove_import", "statement": "use std::io;" }
```

---

### `change_signature`

Replace only the declaration/signature lines, preserving the body.
Use for adding parameters, changing return types, adding generics, etc.

```json
{
  "op": "change_signature",
  "symbol_id": "function:compute",
  "new_signature": "def compute(x: int, y: int = 0) -> int:"
}
```

Multi-line signatures are supported — use `\n` in the string.

---

### `add_decorator`

Prepend a decorator (Python: `@foo`) or attribute (Rust: `#[attr]`) above
a symbol's prefix.

```json
{ "op": "add_decorator", "symbol_id": "function:handler", "decorator": "@login_required" }
{ "op": "add_decorator", "symbol_id": "struct:Config", "decorator": "#[derive(Clone)]" }
```

Supported languages: **Python**, **Rust**.

---

## Symbol ID quick reference

```
"compute"               bare name — unambiguous only
"MyClass.run"           qualified name
"function:compute"      type-qualified — preferred for unambiguous intent
"fn:compute"            alias — expands to function:compute
"class:MyService"
"cls:MyService"         alias — expands to class:MyService
"interface:User"        TypeScript
"enum:Direction"        TypeScript / Rust
"struct:Point"          Rust
"trait:Shape"           Rust
"impl:Point"            Rust
"rule:.hero"            CSS selector
"rule:@media (max-width: 768px)"   CSS @-rule
"tag:hero"              HTML — id="hero"
"tag:main"              HTML — semantic <main>
```
