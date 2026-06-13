# Review Scorecard — Quick Reference

Score each rule: **Pass**, **Warn** (documented deviation), **Fail** (unaddressed violation).

Compliance: all MUST rules Pass; all SHOULD rules Pass or documented.

## Part I — Type Safety and Precision

| #  | Rule                                    | Tier   | Score |
|----|-----------------------------------------|--------|-------|
| 1  | Every field has a single unambiguous type | MUST   |       |
| 2  | Constraints live in the schema           | MUST   |       |
| 3  | Enums: closed, versioned, not overloaded | MUST   |       |
| 4  | Nullable ≠ optional ≠ absent             | MUST   |       |
| 5  | Arrays: item type + cardinality + order  | MUST   |       |
| 6  | Temporal: precision, timezone, format    | MUST   |       |
| 7  | Numeric units declared                   | MUST   |       |
| 8  | Polymorphism: explicit discriminator     | MUST   |       |
| 9  | Defaults declared in schema              | SHOULD |       |

## Part II — Identity and Relationships

| #  | Rule                                     | Tier   | Score |
|----|------------------------------------------|--------|-------|
| 10 | Stable, opaque identity                   | MUST   |       |
| 11 | Relationships navigable in ≥1 direction   | MUST   |       |
| 12 | Composition / aggregation / association explicit | MUST |  |
| 13 | FK targets declared                       | MUST   |       |
| 14 | Cyclic graph constraints declared         | MUST   |       |

## Part III — Normalization and Coherence

| #  | Rule                                     | Tier   | Score |
|----|------------------------------------------|--------|-------|
| 15 | Single source of truth per fact           | MUST   |       |
| 16 | No bag-of-arrays entities                 | SHOULD |       |
| 17 | Cross-cutting types defined once          | SHOULD |       |
| 18 | Computed vs. stored distinguished         | SHOULD |       |

## Part IV — Evolution and Compatibility

| #  | Rule                                     | Tier   | Score |
|----|------------------------------------------|--------|-------|
| 19 | Explicit, monotonic versioning            | MUST   |       |
| 20 | No duplicate-version entities             | MUST   |       |
| 21 | Breaking changes classified               | MUST   |       |
| 22 | Field deprecation annotated               | MUST   |       |

## Part V — Operational Annotations

| #  | Rule                                     | Tier   | Score |
|----|------------------------------------------|--------|-------|
| 23 | Sensitive fields classified               | MUST*  |       |
| 24 | Identity/provenance immutability          | SHOULD |       |
| 25 | Localization strategy declared            | SHOULD |       |
| 26 | Multi-actor provenance metadata           | SHOULD |       |

*Rule 23 is MUST for PII-bearing schemas, MAY otherwise.

## Part VI — Documentation and Generability

| #  | Rule                                     | Tier   | Score |
|----|------------------------------------------|--------|-------|
| 27 | Consistent naming                         | MUST   |       |
| 28 | Mechanically generatable validators       | MUST   |       |
| 29 | Intentional extension points              | MUST   |       |
| 30 | Access patterns don't dictate structure   | SHOULD |       |
| 31 | Readable as standalone artifact           | MUST   |       |

## Totals

- MUST Pass: ___/20 (or ___/19 if no PII)
- SHOULD Pass or Documented: ___/11

## Compatibility Classification (quick ref)

| Change                            | Safe?    |
|-----------------------------------|----------|
| Add optional field                | ✅ Safe  |
| Add required field WITH default   | ⚠️ Caution |
| Add required field WITHOUT default| ❌ Breaking |
| Remove optional field             | ⚠️ Caution |
| Remove required field             | ❌ Breaking |
| Widen enum (add value)            | ⚠️ Caution |
| Narrow enum (remove value)        | ❌ Breaking |
| Relax constraint (widen range)    | ⚠️ Caution |
| Tighten constraint (narrow range) | ❌ Breaking |
| Change field type                 | ❌ Breaking |
| Rename field                      | ❌ Breaking |

Breaking changes → increment major version.
Non-breaking changes → increment minor version.
Annotation-only changes → increment patch version.
