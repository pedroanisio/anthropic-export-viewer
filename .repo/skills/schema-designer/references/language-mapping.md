# Schema Language Mapping — Quick Reference

How to express each design concept in common schema languages.

| Concept | JSON Schema | TypeScript/Zod | Protobuf | SQL DDL | Avro |
|---------|-------------|----------------|----------|---------|------|
| Unambiguous type (R1) | `type` keyword | Type literal | Message/scalar | Column type | Named type |
| Constraints (R2) | `minimum`, `pattern` | `.min()`, `.regex()` | Custom options | `CHECK` constraint | `logicalType` |
| Closed enum (R3) | `enum` keyword | `z.enum()` | `enum` | `ENUM` / `CHECK` | `enum` |
| Nullable (R4) | `type: [T, "null"]` | `T \| null` | `optional` + wrapper | `NULL` / `NOT NULL` | `["null", T]` |
| Array cardinality (R5) | `minItems`, `maxItems` | `.min()`, `.max()` | N/A (repeated) | N/A (app layer) | N/A |
| Temporal format (R6) | `format: "date-time"` | `z.string().datetime()` | `google.protobuf.Timestamp` | `TIMESTAMP WITH TIME ZONE` | `timestamp-millis` |
| Discriminator (R8) | `discriminator` + `oneOf` | `z.discriminatedUnion()` | `oneof` | Inheritance / type column | `union` |
| Default (R9) | `default` keyword | `.default()` | `default` value | `DEFAULT` clause | `default` |
| FK reference (R13) | `$ref` or `x-fk` | Custom branded type | N/A (app layer) | `REFERENCES` | N/A |
| Deprecation (R22) | `deprecated: true` | `.describe("DEPRECATED")` | `[deprecated = true]` | Comment convention | `@deprecated` |
| Sensitivity (R23) | `x-sensitivity` | Custom metadata | Custom options | Column comment | Custom `logicalType` |
| Immutability (R24) | `readOnly: true` | `readonly` modifier | N/A (app layer) | Trigger / policy | N/A |

## Custom Annotations (x- extensions)

When the schema language lacks native support, use these annotation patterns:

| Annotation | Purpose | Example |
|---|---|---|
| `x-fk` | Foreign key target | `x-fk: "User.id"` |
| `x-fk-external` | FK to entity outside this schema | `x-fk-external: true` |
| `x-ordering` | Array ordering semantics | `significant` / `insignificant` |
| `x-timezone` | Temporal timezone handling | `UTC` / `local-with-offset` |
| `x-precision` | Temporal precision | `seconds` / `milliseconds` |
| `x-unit` | Numeric unit | `milliseconds` / `kg` / `cents` |
| `x-sensitivity` | Data classification | `pii` / `phi` / `credential` |
| `x-immutable` | Write-once field | `true` |
| `x-derivation` | Computed field strategy | `source-of-truth` / `derived-cached` / `override-if-present` |
| `x-derived-from` | Source of derived value | `"Entity.field"` |
| `x-graph-constraint` | Reference graph topology | `DAG` / `allow-cycles` |
| `x-max-depth` | Max traversal depth | `5` |
| `x-extension-point` | Intentional escape hatch | `true` |
| `x-deprecated` | Deprecation flag | `true` |
| `x-deprecated-since` | Version when deprecated | `"2.3.0"` |
| `x-replaced-by` | Successor field/entity | `"response_config.format"` |
| `x-sunset` | Removal target version | `"4.0.0"` |
| `x-localization` | i18n strategy | `locale-map` / `single-locale` / `locale-per-entity` |
| `x-denormalized-from` | Denormalization source | `"Entity.field"` |
| `x-canonical` | Authoritative version flag | `true` |
| `x-waiver` | Rule exception documentation | `{ rule: 5, reason: "...", approved_by: "..." }` |
