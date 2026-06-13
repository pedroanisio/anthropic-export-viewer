/**
 * Claim Formalization Schema (CFS) — Zod v4 Definition
 *
 * Module version: 0.0.2
 * Implements spec: CFS v0.5.0
 *
 * DISCLAIMER:
 * No information validated by this schema should be taken for granted.
 * Any statement or premise in a conforming instance not backed by a
 * real logical definition or verifiable reference may be invalid,
 * erroneous, or a hallucination. This schema validates structure,
 * not truth.
 *
 * ARCHITECTURE:
 * Two-pass validation pipeline:
 *   Pass 1 — Zod structural parse: V1–V7, V13–V21 (type + shape checks)
 *   Pass 2 — Programmatic validate(): V4 (uniqueness), V8–V12 (refs), L1–L10
 *
 * The disclaimer (§3 of the spec) is a human-facing governance artifact
 * carried as a YAML comment. YAML parsers strip comments, so disclaimer
 * conformance is a human Review-tier check (R9), not a machine invariant.
 *
 * DEFAULTS BEHAVIOR (verified on Zod 4.3.6):
 * Fields using `.default(x).optional()` correctly materialize `x` when
 * the field is absent from input. Tooling receives the default value,
 * never `undefined`, satisfying the spec's "omission == explicit default"
 * rule.
 *
 * @module cfs
 * @version 0.0.2
 * @license MIT
 */

import { z } from "zod";

// ============================================================================
// §1  VERSIONING
// ============================================================================

/** Module version — independent of spec version. */
export const MODULE_VERSION = "0.0.2" as const;

/** Spec versions this module can validate. */
export const SUPPORTED_SPEC_VERSIONS = ["0.5.0"] as const;

// ============================================================================
// §2  ID PATTERNS
// ============================================================================

const RESERVED_ID = /^[PRQSA]\d+$/;

export const PropositionId = z.string().regex(/^P\d+$/, "Must match P<number>");
export const RuleId = z.string().regex(/^R\d+$/, "Must match R<number>");
export const QuestionId = z.string().regex(/^Q\d+$/, "Must match Q<number>");
export const SilenceId = z.string().regex(/^S\d+$/, "Must match S<number>");
export const AxiomId = z.string().regex(/^A\d+$/, "Must match A<number>");

export const EntityId = z
  .string()
  .regex(/^[A-Z][A-Z0-9_]*$/, "Must be UPPER_SNAKE_CASE")
  .refine((id) => !RESERVED_ID.test(id), {
    message: "Entity ID must not collide with reserved P/R/Q/S/A prefixes",
  });

/**
 * IDs valid in Question.related arrays.
 * Per spec §4.5: PropositionID | RuleID | EntityID | SilenceID | AxiomID.
 * QuestionID is NOT included.
 */
const RelatedId = z
  .string()
  .regex(/^[A-Z][A-Z0-9_]*$|^[PRSA]\d+$/)
  .refine((id) => !/^Q\d+$/.test(id), {
    message: "Question.related cannot reference other QuestionIDs (spec §4.5)",
  });

// ============================================================================
// §3  ENUMS
// ============================================================================

export const SourceKind = z.enum([
  "journalism", "technical_documentation", "legal_filing", "policy_paper",
  "transcript", "academic_paper", "fiction", "scripture", "other",
]);

export const TruthRegime = z.enum(["realist", "diegetic", "mixed", "scriptural"]);

export const NarratorReliability = z.enum([
  "reliable", "unreliable", "indeterminate", "divinely_authorized",
]);

export const EntityType = z.enum([
  "Person", "Organization", "Government_Agency", "Software_System",
  "Software_Module", "Hardware", "Document", "Event", "Editorial_Voice",
  "Place", "Polity", "Collective", "Manifestation",
]);

export const OntologicalStatus = z.enum([
  "real", "fictional", "semi_fictional", "disputed", "traditional",
]);

export const SpeechAct = z.enum([
  "assertion", "directive", "recommendation", "definition", "editorial",
  "prediction", "narration", "characterization", "figuration", "revelation",
]);

export const Verifiability = z.enum([
  "machine_verifiable", "empirically_testable", "expert_judgment",
  "unfalsifiable", "diegetic_fact", "diegetic_testimony", "traditional_doctrine",
]);

export const Fidelity = z.enum([
  "verbatim_quote", "close_paraphrase", "loose_paraphrase",
  "editorial_synthesis", "authorial_construction",
]);

export const RelationType = z.enum([
  "entails", "motivates", "contradicts", "weakens", "strengthens",
  "is_consistent_with", "presupposes", "refines", "mirrors",
]);

export const QuestionKind = z.enum(["factual", "conceptual", "methodological", "ethical"]);

export const SilenceKind = z.enum([
  "absent_perspective", "unasked_question", "suppressed_counter", "missing_context",
]);

// ============================================================================
// §4  COMPOUND TYPES
// ============================================================================

export const NarrativeLayer = z.object({
  narrator: EntityId,
  audience: EntityId.optional(),
  reliability: NarratorReliability,
  note: z.string().optional(),
});

export const NarrativeFrame = z.object({
  layers: z.array(NarrativeLayer).min(1),
});

export const ProvenanceHop = z.object({
  speaker: EntityId,
  medium: z.string().optional(),
});

/** Flat array, outer→inner. Min 2 elements (V20). */
export const ProvenanceChain = z.array(ProvenanceHop).min(2);

// ============================================================================
// §5  PUBLISHED DATE
// ============================================================================

const ISO_DATETIME = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

const Published = z.string().refine(
  (v) =>
    v === "undated" ||
    /^\d{4}$/.test(v) ||
    /^\d{4}-(0[1-9]|1[0-2])$/.test(v) ||
    /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(v) ||
    ISO_DATETIME.test(v),
  { message: "Must be YYYY, YYYY-MM, YYYY-MM-DD, full ISO 8601 datetime, or 'undated'" }
);

// ============================================================================
// §6  META
// ============================================================================

export const Meta = z
  .object({
    source: z.string().min(1),
    author: z.array(z.string().min(1)).min(1),
    published: Published,
    title: z.string().min(1),
    source_kind: SourceKind,
    truth_regime: TruthRegime,
    locator: z.string().optional(),
    narrative_frame: NarrativeFrame.optional(),
    note: z.string().optional(),
  })
  .refine(
    (meta) => {
      const kindRequires = meta.source_kind === "fiction" || meta.source_kind === "scripture";
      const regimeRequires = meta.truth_regime === "diegetic" || meta.truth_regime === "scriptural";
      if ((kindRequires || regimeRequires) && !meta.narrative_frame) {
        return false;
      }
      return true;
    },
    { message: "narrative_frame required when source_kind is fiction/scripture or truth_regime is diegetic/scriptural (V17)" }
  );

// ============================================================================
// §7  ENTITY
// ============================================================================

export const Entity = z.object({
  id: EntityId,
  type: EntityType,
  ontological_status: OntologicalStatus.default("real").optional(),
  roles: z.array(z.string()).default([]).optional(),
  affiliations: z.array(EntityId).default([]).optional(),
  domain: z.string().optional(),
  developer: EntityId.optional(),
  parent: EntityId.optional(),
  founder: EntityId.optional(),
  associated_with: EntityId.optional(),
  location: EntityId.optional(),
  note: z.string().optional(),
});

// ============================================================================
// §8  PROPOSITION
// ============================================================================

export const Proposition = z
  .object({
    id: PropositionId,
    speaker: EntityId,
    medium: z.string().optional(),
    claim: z.string().min(1),
    speech_act: SpeechAct,
    verifiability: Verifiability.optional(),
    /**
     * How faithfully the source document renders this claim.
     * Describes the OUTERMOST relay's treatment — how the source being
     * formalized presents the material. Does NOT describe intermediate
     * relay fidelity in multi-hop provenance chains.
     */
    fidelity: Fidelity.optional(),
    provenance: ProvenanceChain.optional(),
    literal: z.boolean().default(true).optional(),
    anchor: z.string().optional(),
    note: z.string().optional(),
  })
  .refine(
    (p) => {
      if (p.speech_act === "figuration" && p.literal !== false) return false;
      return true;
    },
    { message: "speech_act 'figuration' requires literal: false (V18)" }
  )
  .refine(
    (p) => {
      const firstHop = p.provenance?.[0];
      if (firstHop) {
        return firstHop.speaker === p.speaker;
      }
      return true;
    },
    { message: "provenance[0].speaker must equal proposition speaker (V19)" }
  );

// ============================================================================
// §9  AXIOM
// ============================================================================

export const Axiom = z.object({
  id: AxiomId,
  name: z.string().min(1),
  definition: z.string().min(1),
  domain: z.string().optional(),
  controversial: z.boolean().default(false).optional(),
  note: z.string().optional(),
});

// ============================================================================
// §10  RULE
// ============================================================================

const RuleOperand = z.string().regex(/^[PA]\d+$/, "Rule operands must be P<n> or A<n>");

export const Rule = z.object({
  id: RuleId,
  name: z.string().min(1),
  relation_type: RelationType,
  /** Distributive: relation applies independently to each antecedent. */
  antecedent_ids: z.array(RuleOperand).min(1),
  /** Distributive: relation applies independently to each consequent. */
  consequent_ids: z.array(RuleOperand).min(1),
  /** Non-normative human-readable symbolic expression. */
  form: z.string().optional(),
  plain: z.string().min(1),
  analytic_framework: z.string().optional(),
  note: z.string().optional(),
});

// ============================================================================
// §11  QUESTION
// ============================================================================

export const Question = z.object({
  id: QuestionId,
  question: z.string().min(1),
  kind: QuestionKind,
  related: z.array(RelatedId).min(1),
});

// ============================================================================
// §12  SILENCE
// ============================================================================

export const Silence = z.object({
  id: SilenceId,
  kind: SilenceKind,
  description: z.string().min(1),
  affected_entities: z.array(EntityId).default([]).optional(),
  related_propositions: z.array(PropositionId).min(1),
  note: z.string().optional(),
});

// ============================================================================
// §13  TOP-LEVEL INSTANCE
// ============================================================================

export const CfsInstance = z.object({
  schema_version: z.enum(SUPPORTED_SPEC_VERSIONS),
  meta: Meta,
  entities: z.array(Entity).min(1),
  propositions: z.array(Proposition).min(1),
  axioms: z.array(Axiom),
  rules: z.array(Rule).min(1),
  open_questions: z.array(Question).min(1),
  silences: z.array(Silence).optional(),
});

// ============================================================================
// §14  INFERRED TYPES
// ============================================================================

export type SourceKind = z.infer<typeof SourceKind>;
export type TruthRegime = z.infer<typeof TruthRegime>;
export type NarratorReliability = z.infer<typeof NarratorReliability>;
export type EntityType = z.infer<typeof EntityType>;
export type OntologicalStatus = z.infer<typeof OntologicalStatus>;
export type SpeechAct = z.infer<typeof SpeechAct>;
export type Verifiability = z.infer<typeof Verifiability>;
export type Fidelity = z.infer<typeof Fidelity>;
export type RelationType = z.infer<typeof RelationType>;
export type QuestionKind = z.infer<typeof QuestionKind>;
export type SilenceKind = z.infer<typeof SilenceKind>;
export type NarrativeLayer = z.infer<typeof NarrativeLayer>;
export type NarrativeFrame = z.infer<typeof NarrativeFrame>;
export type ProvenanceHop = z.infer<typeof ProvenanceHop>;
export type Meta = z.infer<typeof Meta>;
export type Entity = z.infer<typeof Entity>;
export type Proposition = z.infer<typeof Proposition>;
export type Axiom = z.infer<typeof Axiom>;
export type Rule = z.infer<typeof Rule>;
export type Question = z.infer<typeof Question>;
export type Silence = z.infer<typeof Silence>;
export type CfsInstance = z.infer<typeof CfsInstance>;

// ============================================================================
// §15  VALIDATION TYPES
// ============================================================================

export interface ValidationError { rule: string; message: string; path?: string; }
export interface LintWarning { rule: string; message: string; path?: string; }
export interface ValidationResult { valid: boolean; errors: ValidationError[]; warnings: LintWarning[]; }

function validationError(rule: string, message: string, path?: string): ValidationError {
  return path === undefined ? { rule, message } : { rule, message, path };
}

function lintWarning(rule: string, message: string, path?: string): LintWarning {
  return path === undefined ? { rule, message } : { rule, message, path };
}

// ============================================================================
// §16  REFERENTIAL INTEGRITY + LINT (V4, V8–V12, L1–L10)
// ============================================================================

export function validate(instance: CfsInstance): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: LintWarning[] = [];

  const entityIds = new Set(instance.entities.map((e) => e.id));
  const propIds = new Set(instance.propositions.map((p) => p.id));
  const axiomIds = new Set(instance.axioms.map((a) => a.id));
  const ruleIds = new Set(instance.rules.map((r) => r.id));
  const silenceIds = new Set((instance.silences ?? []).map((s) => s.id));

  const propMap = new Map(instance.propositions.map((p) => [p.id, p]));
  const axiomMap = new Map(instance.axioms.map((a) => [a.id, a]));

  const chk = (ok: boolean, rule: string, msg: string, path?: string) => {
    if (!ok) errors.push(validationError(rule, msg, path));
  };

  // --- V4: Uniqueness (all 6 namespaces) ---
  function checkDuplicates(items: Array<{ id: string }>, ns: string) {
    const seen = new Set<string>();
    for (const { id } of items) {
      if (seen.has(id)) errors.push({ rule: "V4", message: `Duplicate ${ns} ID "${id}"` });
      seen.add(id);
    }
  }
  checkDuplicates(instance.entities, "entity");
  checkDuplicates(instance.propositions, "proposition");
  checkDuplicates(instance.axioms, "axiom");
  checkDuplicates(instance.rules, "rule");
  checkDuplicates(instance.open_questions, "question");
  checkDuplicates(instance.silences ?? [], "silence");

  // --- V8: Entity refs ---
  const chkE = (id: string, path: string) => chk(entityIds.has(id), "V8", `Undeclared EntityID "${id}"`, path);

  for (const e of instance.entities) {
    for (const a of e.affiliations ?? []) chkE(a, `entities/${e.id}/affiliations`);
    if (e.developer) chkE(e.developer, `entities/${e.id}/developer`);
    if (e.parent) chkE(e.parent, `entities/${e.id}/parent`);
    if (e.founder) chkE(e.founder, `entities/${e.id}/founder`);
    if (e.associated_with) chkE(e.associated_with, `entities/${e.id}/associated_with`);
    if (e.location) chkE(e.location, `entities/${e.id}/location`);
  }
  for (const p of instance.propositions) {
    chkE(p.speaker, `propositions/${p.id}/speaker`);
    for (const [i, provenance] of (p.provenance ?? []).entries()) {
      chkE(provenance.speaker, `propositions/${p.id}/provenance[${i}]`);
    }
  }
  if (instance.meta.narrative_frame) {
    for (const [i, layer] of instance.meta.narrative_frame.layers.entries()) {
      chkE(layer.narrator, `meta/narrative_frame/layers[${i}]/narrator`);
      if (layer.audience) chkE(layer.audience, `meta/narrative_frame/layers[${i}]/audience`);
    }
  }

  // --- V9 + V10: Rule operands ---
  for (const r of instance.rules) {
    for (const id of r.antecedent_ids) {
      if (id.startsWith("P")) chk(propIds.has(id), "V9", `Undeclared "${id}"`, `rules/${r.id}/antecedent_ids`);
      else if (id.startsWith("A")) chk(axiomIds.has(id), "V10", `Undeclared "${id}"`, `rules/${r.id}/antecedent_ids`);
    }
    for (const id of r.consequent_ids) {
      if (id.startsWith("P")) chk(propIds.has(id), "V9", `Undeclared "${id}"`, `rules/${r.id}/consequent_ids`);
      else if (id.startsWith("A")) chk(axiomIds.has(id), "V10", `Undeclared "${id}"`, `rules/${r.id}/consequent_ids`);
    }
  }

  // --- V9 + V11: Question related (dispatched by prefix) ---
  for (const q of instance.open_questions) {
    for (const id of q.related) {
      if (/^P\d+$/.test(id)) chk(propIds.has(id), "V9", `Undeclared "${id}"`, `questions/${q.id}/related`);
      else if (/^R\d+$/.test(id)) chk(ruleIds.has(id), "V11", `Undeclared "${id}"`, `questions/${q.id}/related`);
      else if (/^S\d+$/.test(id)) chk(silenceIds.has(id), "V11", `Undeclared "${id}"`, `questions/${q.id}/related`);
      else if (/^A\d+$/.test(id)) chk(axiomIds.has(id), "V10", `Undeclared "${id}"`, `questions/${q.id}/related`);
      else chkE(id, `questions/${q.id}/related`);
    }
  }

  // --- V8 + V9: Silence refs (including related_propositions per V9) ---
  for (const s of instance.silences ?? []) {
    for (const id of s.affected_entities ?? []) chkE(id, `silences/${s.id}/affected_entities`);
    for (const id of s.related_propositions) chk(propIds.has(id), "V9", `Undeclared "${id}"`, `silences/${s.id}/related_propositions`);
  }

  // =========================================================================
  // LINT (L1–L10)
  // =========================================================================
  const regime = instance.meta.truth_regime;
  const warn = (rule: string, msg: string, path?: string) => warnings.push(lintWarning(rule, msg, path));

  // L1: scriptural + machine_verifiable
  if (regime === "scriptural") {
    for (const p of instance.propositions) {
      if (p.verifiability === "machine_verifiable") warn("L1", `${p.id} is machine_verifiable under scriptural`, `propositions/${p.id}`);
    }
  }

  // L2: diegetic + machine_verifiable
  if (regime === "diegetic") {
    for (const p of instance.propositions) {
      if (p.verifiability === "machine_verifiable") warn("L2", `${p.id} is machine_verifiable under diegetic`, `propositions/${p.id}`);
    }
  }

  // L3: entails from unfalsifiable (NOTE: axioms lack verifiability, so propMap miss = correct skip)
  for (const r of instance.rules) {
    if (r.relation_type === "entails") {
      for (const id of r.antecedent_ids) {
        const prop = propMap.get(id);
        if (prop?.verifiability === "unfalsifiable") warn("L3", `Rule ${r.id} entails from unfalsifiable ${id}`, `rules/${r.id}`);
      }
    }
  }

  // L4: non-literal assertion/definition
  for (const p of instance.propositions) {
    if (p.literal === false && (p.speech_act === "assertion" || p.speech_act === "definition")) {
      warn("L4", `${p.id} is non-literal ${p.speech_act}`, `propositions/${p.id}`);
    }
  }

  // L5: form arrow ↔ relation_type mismatch (heuristic)
  const ARROWS: Record<string, string> = {
    entails: "→", motivates: "⇝", contradicts: "⇄", weakens: "↓",
    strengthens: "↑", is_consistent_with: "∥", presupposes: "⊲", refines: "≻", mirrors: "⇔",
  };
  for (const r of instance.rules) {
    if (r.form) {
      const expected = ARROWS[r.relation_type];
      if (expected && !r.form.includes(expected)) {
        warn("L5", `Rule ${r.id} form lacks expected '${expected}' for ${r.relation_type}`, `rules/${r.id}/form`);
      }
    }
  }

  // L6: deep provenance (> 4 hops)
  for (const p of instance.propositions) {
    if (p.provenance && p.provenance.length > 4) warn("L6", `${p.id} has ${p.provenance.length}-hop provenance`, `propositions/${p.id}`);
  }

  // L7: revelation without authority role (extensible heuristic)
  const AUTH = /\b(god|prophet|avatar|divine|whistleblower|oracle|sage|guru|priest|rabbi|imam|messiah|angel|bodhisattva)\b/i;
  for (const p of instance.propositions) {
    if (p.speech_act === "revelation") {
      const ent = instance.entities.find((e) => e.id === p.speaker);
      if (!(ent?.roles ?? []).some((r) => AUTH.test(r))) {
        warn("L7", `${p.id} uses 'revelation' but ${p.speaker} lacks authority role`, `propositions/${p.id}`);
      }
    }
  }

  // L8: controversial axiom in rule (either side)
  for (const r of instance.rules) {
    for (const id of [...r.antecedent_ids, ...r.consequent_ids]) {
      const ax = axiomMap.get(id);
      if (ax?.controversial) warn("L8", `Rule ${r.id} involves controversial axiom ${id}`, `rules/${r.id}`);
    }
  }

  // L9: traditional_doctrine only valid under scriptural/mixed
  if (regime !== "scriptural" && regime !== "mixed") {
    for (const p of instance.propositions) {
      if (p.verifiability === "traditional_doctrine") {
        warn("L9", `${p.id} has traditional_doctrine under ${regime} truth_regime`, `propositions/${p.id}`);
      }
    }
  }

  // L10: cross-regime entailment (diegetic/scriptural antecedent → realist consequent) under mixed
  if (regime === "mixed") {
    const DIEGETIC = new Set(["diegetic_fact", "diegetic_testimony", "traditional_doctrine"]);
    const REALIST = new Set(["machine_verifiable", "empirically_testable"]);
    for (const r of instance.rules) {
      if (r.relation_type === "entails") {
        const allAntDiegetic = r.antecedent_ids.every((id) => {
          const p = propMap.get(id);
          return p?.verifiability && DIEGETIC.has(p.verifiability);
        });
        const anyConsRealist = r.consequent_ids.some((id) => {
          const p = propMap.get(id);
          return p?.verifiability && REALIST.has(p.verifiability);
        });
        if (allAntDiegetic && anyConsRealist) {
          warn("L10", `Rule ${r.id} entails realist from diegetic/scriptural antecedents`, `rules/${r.id}`);
        }
      }
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ============================================================================
// §17  CONVENIENCE PIPELINE
// ============================================================================

export interface FullValidationResult extends ValidationResult {
  data?: CfsInstance;
  parseError?: z.ZodError;
}

export function parseCfs(raw: unknown): FullValidationResult {
  const parseResult = CfsInstance.safeParse(raw);
  if (!parseResult.success) {
    return {
      valid: false,
      errors: parseResult.error.issues.map((issue) => ({
        rule: "PARSE",
        message: issue.message,
        path: issue.path.join("/"),
      })),
      warnings: [],
      parseError: parseResult.error,
    };
  }
  const refResult = validate(parseResult.data);
  return { ...refResult, data: parseResult.data };
}
