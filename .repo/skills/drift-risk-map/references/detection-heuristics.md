# Detection Heuristics

Concrete file patterns, commands, and signals for each coupling domain.
Organized by domain, then by ecosystem where specifics diverge.

These are heuristics, not proofs. A matching pattern means "investigate
further", not "coupling confirmed". Always open the file and verify.

---

## Table of Contents

1. [API contract ↔ SDK / client codegen](#1-api-contract--sdk--client-codegen)
2. [API contract ↔ request/response validation](#2-api-contract--requestresponse-validation)
3. [Data models ↔ DB schema / migrations](#3-data-models--db-schema--migrations)
4. [Data models ↔ serializers / DTOs](#4-data-models--serializers--dtos)
5. [Public interfaces ↔ documentation](#5-public-interfaces--documentation)
6. [Config / env ↔ runtime consumers](#6-config--env--runtime-consumers)
7. [Shared types / constants ↔ import sites](#7-shared-types--constants--import-sites)
8. [Infra-as-Code ↔ application expectations](#8-infra-as-code--application-expectations)
9. [Test fixtures / mocks ↔ production schemas](#9-test-fixtures--mocks--production-schemas)
10. [Cross-cutting detection commands](#10-cross-cutting-detection-commands)

---

## 1. API contract ↔ SDK / client codegen

### Detect source specs

```bash
# OpenAPI / Swagger
find . -type f \( -name "openapi.*" -o -name "swagger.*" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*"
find . -type f -name "*.yaml" -o -name "*.yml" | \
  xargs grep -l "openapi:" 2>/dev/null
find . -type f -name "*.json" | \
  xargs grep -l '"openapi"' 2>/dev/null

# Protobuf
find . -type f -name "*.proto" -not -path "*/node_modules/*"

# GraphQL SDL
find . -type f \( -name "*.graphql" -o -name "*.gql" \) \
  -not -path "*/node_modules/*"

# gRPC / buf
find . -name "buf.yaml" -o -name "buf.gen.yaml" -o -name "buf.work.yaml"
```

### Detect codegen configs

```bash
# OpenAPI codegen
find . -name "openapitools.json" -o -name ".openapi-generator" -type d
find . -name "openapi-generator-cli*"
grep -rl "openapi-generator" package.json Makefile justfile 2>/dev/null

# GraphQL codegen
find . -name "codegen.ts" -o -name "codegen.yml" -o -name ".graphqlrc*"
grep -rl "@graphql-codegen" package.json 2>/dev/null

# Protobuf codegen
find . -name "buf.gen.yaml"
grep -rl "protoc\|protobuf" Makefile justfile 2>/dev/null

# Generic: directories commonly holding generated code
find . -type d \( -name "generated" -o -name "__generated__" \
  -o -name "gen" -o -name "sdk" \) -not -path "*/node_modules/*"
```

### Detect manual mirrors (highest risk)

Look for hand-written HTTP clients that hardcode paths from the API spec:

```bash
# TypeScript/JavaScript
grep -rn "fetch\|axios\|got\|ky\|superagent" src/ --include="*.ts" \
  --include="*.js" | grep -i "api\|endpoint\|/v[0-9]"

# Python
grep -rn "requests\.\(get\|post\|put\|patch\|delete\)\|httpx\.\|aiohttp" \
  --include="*.py" | grep -v "test"

# Go
grep -rn 'http\.\(Get\|Post\|NewRequest\)' --include="*.go" | grep -v "_test"
```

If these clients exist AND a spec file also exists, the coupling is likely
manual-mirror unless there's an import chain from generated code.

### Guard detection

```bash
# Check CI for codegen freshness
grep -rn "openapi-generator\|buf generate\|graphql-codegen" \
  .github/workflows/ .gitlab-ci.yml Makefile justfile 2>/dev/null

# Check for "generated" markers in files
head -5 <suspected-generated-file> | grep -i "generated\|auto-generated\|DO NOT EDIT"
```

---

## 2. API contract ↔ request/response validation

### Python

```bash
# Pydantic models used as request/response types
grep -rn "class.*BaseModel\|class.*BaseSchema" --include="*.py"

# FastAPI route signatures (Pydantic coupling)
grep -rn "def.*app\.\(get\|post\|put\|delete\|patch\)" --include="*.py"

# Marshmallow schemas
grep -rn "class.*Schema.*Ma\|fields\." --include="*.py" | head -20

# DRF serializers
grep -rn "class.*Serializer" --include="*.py"
```

### TypeScript / JavaScript

```bash
# Zod schemas
grep -rn "z\.object\|z\.string\|z\.number\|zodResolver" \
  --include="*.ts" --include="*.tsx"

# class-validator decorators
grep -rn "@IsString\|@IsNumber\|@IsEmail\|@ValidateNested" \
  --include="*.ts"

# Joi schemas
grep -rn "Joi\.\(object\|string\|number\)" --include="*.ts" --include="*.js"

# io-ts / Effect Schema
grep -rn "t\.type\|t\.interface\|S\.struct" --include="*.ts"
```

### Risk signal: duplicated shape definitions

If validation schemas are defined in different files from the API route
types, and there is no shared import or codegen link between them, flag
as **manual-mirror**.

```bash
# Find files defining both a route AND a schema in the same module
# vs. files where they're split — split = higher drift risk
```

---

## 3. Data models ↔ DB schema / migrations

### Detect ORM models

```bash
# SQLAlchemy
grep -rn "class.*Base\)\|Column(\|mapped_column\|DeclarativeBase" \
  --include="*.py"

# Django
grep -rn "class.*models\.Model" --include="*.py"

# Prisma
find . -name "schema.prisma"

# TypeORM
grep -rn "@Entity\|@Column\|@PrimaryGeneratedColumn" --include="*.ts"

# Sequelize
grep -rn "sequelize\.define\|Model\.init" --include="*.ts" --include="*.js"

# Go (GORM)
grep -rn "gorm\.Model\|gorm:\"" --include="*.go"

# ActiveRecord
grep -rn "class.*<.*ActiveRecord::Base\|ApplicationRecord" --include="*.rb"
```

### Detect migration files

```bash
# Alembic (Python)
find . -path "*/alembic/versions/*.py" -o -path "*/migrations/versions/*.py"

# Django migrations
find . -path "*/migrations/0*.py"

# Knex / TypeORM / Sequelize
find . -path "*/migrations/*" -name "*.ts" -o -name "*.js" -o -name "*.sql"

# Flyway / Liquibase
find . -path "*/db/migration/*" -name "*.sql"
find . -name "*.changelog.xml" -o -name "*.changelog.yaml"

# Prisma
find . -path "*/prisma/migrations/*"

# Rails
find . -path "*/db/migrate/*.rb"
```

### Risk signals

- Model has a field with no corresponding column in the most recent migration.
- Migration adds a column with `nullable=False` and no default, but the model
  declares a default that only exists at the application layer.
- Enum values in application code don't match the DB enum constraint.
- Index definitions in the model decorator vs. raw SQL migration diverge.

```bash
# Quick check: compare field names in model vs. latest migration
# (manual inspection usually required, but initial signals)
grep -n "Column\|mapped_column\|Field(" <model_file>
grep -n "add_column\|op\.create_table\|CREATE TABLE" <latest_migration>
```

---

## 4. Data models ↔ serializers / DTOs

### Detect serializer / DTO definitions

```bash
# DRF serializers
grep -rn "class.*Serializer\|class.*ViewSet" --include="*.py"

# Pydantic response models separate from DB models
# Look for Pydantic models NOT used as ORM models
grep -rn "class.*BaseModel" --include="*.py" | grep -v "models\|entities"

# Go: struct tags for JSON marshaling
grep -rn '`json:"' --include="*.go"

# Java: MapStruct mappers
grep -rn "@Mapper\|@Mapping" --include="*.java"

# TypeScript: manual toJSON/fromJSON
grep -rn "toJSON\|fromJSON\|toDto\|fromDto\|serialize\|deserialize" \
  --include="*.ts"
```

### Risk signal: field count mismatch

If a model has N fields and its serializer/DTO has M fields where M ≠ N
(and the difference is not intentionally selective), investigate whether
someone added a model field but forgot the serializer.

---

## 5. Public interfaces ↔ documentation

### Detect documentation artifacts

```bash
# Markdown docs
find . -maxdepth 3 -name "README*" -o -name "CHANGELOG*" \
  -o -name "CONTRIBUTING*" -o -name "API.md"

# Doc site configs
find . -name "mkdocs.yml" -o -name "docusaurus.config.*" \
  -o -name "conf.py" -path "*/docs/*" -o -name "_config.yml" \
  -o -name "antora.yml"

# Man pages
find . -path "*/man/*" -name "*.1" -o -name "*.md"

# CLI help strings (look for discrepancies with docs)
grep -rn "\.option(\|\.command(\|add_argument\|@click\.\|cobra\.Command" \
  --include="*.ts" --include="*.py" --include="*.go" --include="*.js"
```

### Risk signals

- OpenAPI spec exists but is NOT generated from code annotations —
  maintained as a separate YAML file.
- README contains usage examples with function signatures or CLI flags.
  If those signatures change in code, the README silently lies.
- `CHANGELOG.md` is manually maintained (check if it's in `.github/`
  release automation or truly hand-edited).

```bash
# Check if OpenAPI spec is generated or handwritten
# Generated specs often have a generator comment or live in a generated/ dir
head -20 <openapi-file> | grep -i "generated\|auto-generated"

# Check if changelog is automated
grep -rn "changelog\|release-please\|semantic-release\|standard-version" \
  .github/workflows/ package.json 2>/dev/null
```

---

## 6. Config / env ↔ runtime consumers

### Detect config definitions (the "template" side)

```bash
find . -name ".env.example" -o -name ".env.template" -o -name ".env.sample"
find . -name "config.ts" -o -name "config.js" -o -name "settings.py" \
  -o -name "config.go" -o -name "application.properties" \
  -o -name "application.yml"

# Helm values
find . -name "values.yaml" -path "*/helm/*" -o -path "*/chart/*"

# Terraform variables
find . -name "variables.tf"

# Docker Compose env
grep -n "environment:" docker-compose*.yml 2>/dev/null
```

### Detect runtime consumers (the "reader" side)

```bash
# Python
grep -rn "os\.getenv\|os\.environ\|environ\.get\|settings\." \
  --include="*.py" | grep -v "test\|migration"

# TypeScript / JavaScript
grep -rn "process\.env\.\|import.*config" --include="*.ts" --include="*.js" \
  | grep -v "node_modules\|test\|spec"

# Go
grep -rn 'os\.Getenv\|viper\.\|envconfig\.' --include="*.go" | grep -v "_test"

# Java / Kotlin
grep -rn '@Value\|@ConfigurationProperties\|System\.getenv' \
  --include="*.java" --include="*.kt"

# Rust
grep -rn 'std::env::var\|dotenvy\|config::' --include="*.rs"
```

### Risk signal: orphaned or undeclared keys

Extract the key names from both sides and diff them:

```bash
# Example: Python project
# Keys in .env.example
grep -oP '^[A-Z_]+' .env.example | sort > /tmp/defined_keys.txt

# Keys consumed in code
grep -rohP 'os\.getenv\(\s*["\x27]([A-Z_]+)' --include="*.py" -r src/ \
  | grep -oP '[A-Z_]+' | sort -u > /tmp/consumed_keys.txt

# Keys consumed but not defined in template
comm -13 /tmp/defined_keys.txt /tmp/consumed_keys.txt
```

Keys that appear in code but not in the template are a CRITICAL drift vector:
a new deployment will silently get `None`/`undefined`/`""`.

---

## 7. Shared types / constants ↔ import sites

### Detect shared type files

```bash
# Common patterns for shared/central type definitions
find . -path "*/types/*" -o -path "*/shared/*" -o -path "*/common/*" \
  -o -name "types.ts" -o -name "constants.ts" -o -name "enums.py" \
  -o -name "constants.py" | grep -v node_modules | grep -v __pycache__
```

### Detect duplicated definitions (the real risk)

```bash
# String literal unions repeated across files (TypeScript)
grep -rn "type.*=.*|.*|" --include="*.ts" | \
  awk -F: '{print $3}' | sort | uniq -c | sort -rn | head -20

# Enum-like dicts or string sets repeated (Python)
grep -rn "class.*Enum\)\|Literal\[" --include="*.py"

# Magic numbers / string constants defined in more than one file
grep -rn "const.*=.*['\"]" --include="*.ts" | \
  awk -F= '{print $2}' | sort | uniq -c | sort -rn | head -10
```

### Risk signal

If the same logical constant or type is defined in 2+ files with no import
relationship, the coupling is manual-mirror and CRITICAL.

---

## 8. Infra-as-Code ↔ application expectations

### Detect shared references

```bash
# Port numbers appearing in both infra and app code
grep -rn "port\|PORT" --include="*.tf" --include="*.yaml" \
  --include="*.yml" --include="*.ts" --include="*.py" --include="*.go" \
  | grep -v node_modules | grep "[0-9]\{4,5\}"

# Resource names (queues, buckets, topics)
grep -rn "sqs\|sns\|s3\|bucket\|queue\|topic" \
  --include="*.tf" --include="*.ts" --include="*.py" --include="*.go" \
  --include="*.yaml" | grep -v node_modules

# Hostnames and service URLs
grep -rn "localhost\|\.internal\|\.svc\.cluster" \
  --include="*.tf" --include="*.yaml" --include="*.ts" --include="*.py" \
  --include="*.go" | grep -v node_modules
```

### Risk signal

If a Terraform output or Helm value defines a resource name, and application
code references that same name as a string literal (not read from config),
the coupling is manual-mirror. A rename in infra won't cause a build
failure.

---

## 9. Test fixtures / mocks ↔ production schemas

### Detect fixtures

```bash
# JSON fixtures
find . -path "*/fixtures/*" -name "*.json" \
  -o -path "*/test*/*" -name "*.json" \
  -o -path "*/__fixtures__/*"

# Factory definitions
grep -rn "Factory\|factory_boy\|faker\|FactoryBot\|@factory" \
  --include="*.py" --include="*.ts" --include="*.rb" --include="*.js"

# Snapshot files
find . -name "*.snap" -o -name "__snapshots__" -type d

# Seed data
find . -name "seed*" \( -name "*.ts" -o -name "*.py" -o -name "*.sql" \
  -o -name "*.js" \)

# MSW / nock / VCR cassettes
find . -path "*/cassettes/*" -o -path "*/__recordings__/*"
grep -rn "rest\.\(get\|post\)\|nock(" --include="*.ts" --include="*.js" \
  | head -20
```

### Risk signal

If fixture JSON embeds a schema shape (field names, nesting, types) and
there is no generation step that derives fixtures from the production schema,
every schema change silently leaves the fixtures lying. Check for:

```bash
# Is there a fixture generation script?
grep -rn "generate.*fixture\|fixture.*generate\|seed.*generate" \
  Makefile justfile package.json 2>/dev/null
```

If not, flag as HIGH or CRITICAL depending on test coverage breadth.

---

## 10. Cross-cutting detection commands

### Automated guard inventory

Enumerate everything the CI pipeline actually checks:

```bash
# GitHub Actions
find .github/workflows -name "*.yml" -o -name "*.yaml" | \
  xargs grep -h "run:" 2>/dev/null | sed 's/.*run://' | sort -u

# Makefile targets
grep -oP '^[a-zA-Z_-]+:' Makefile 2>/dev/null

# package.json scripts
cat package.json 2>/dev/null | python3 -c \
  "import sys,json; [print(k,v) for k,v in json.load(sys.stdin).get('scripts',{}).items()]"

# Pre-commit hooks
cat .pre-commit-config.yaml 2>/dev/null
```

### Find "DO NOT EDIT" / generated markers

```bash
grep -rl "DO NOT EDIT\|auto-generated\|THIS FILE IS GENERATED\|@generated" \
  --include="*.ts" --include="*.py" --include="*.go" --include="*.java" \
  --include="*.rs" --include="*.js" | grep -v node_modules
```

These files should have a corresponding generation command. If the command
is not in CI, the generated file can drift from its source.
