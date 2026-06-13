// Copyright (c) source-code. Licensed under MIT.
//
// ─────────────────────────────────────────────────────────────────────────────
// Plan Schema
// ─────────────────────────────────────────────────────────────────────────────
//
// Define the operational schema for multi-actor execution plans.
// This module implements the formal constraint model used by planning workflows.
// See docs/_specs/schemas/docs/plan-schema-protocol.md for full protocol notes.

import * as z from "zod";

// ─────────────────────────────────────────────────────────────────────────────
// § 0  PRIMITIVES & BRANDED IDENTIFIERS
// ─────────────────────────────────────────────────────────────────────────────

const Timestamp = z.string().datetime({ offset: true });
const GitSha = z.string().regex(/^[0-9a-f]{7,40}$/, "Must be a valid git SHA (7-40 hex chars)");
const SemVer = z.string().regex(/^\d+\.\d+\.\d+(-[\w.]+)?$/, "Must be valid semver");
const GlobPattern = z.string().min(1);
const ShellCommand = z.string().min(1);
const TokenCount = z.number().int().nonnegative();

const ActorId = z.string().min(1).brand("ActorId");
const StepId = z.string().min(1).brand("StepId");
const RiskId = z.string().min(1).brand("RiskId");
const DecisionId = z.string().min(1).brand("DecisionId");
const ScopeZoneId = z.string().min(1).brand("ScopeZoneId");
const ResourceId = z.string().min(1).brand("ResourceId");

type ActorId = z.infer<typeof ActorId>;
type StepId = z.infer<typeof StepId>;
type RiskId = z.infer<typeof RiskId>;
type DecisionId = z.infer<typeof DecisionId>;
type ScopeZoneId = z.infer<typeof ScopeZoneId>;
type ResourceId = z.infer<typeof ResourceId>;

// ─────────────────────────────────────────────────────────────────────────────
// § 1  RESOURCES  [FM §1.1 — R]
//
// Promoted to first-class entities with size estimates, enabling
// capacity feasibility [Def 3.3, condition A1] and thrashing detection [Prop 2.8].
// ─────────────────────────────────────────────────────────────────────────────

const Resource = z.object({
  id: ResourceId,
  path: z.string().min(1),
  /**
   * Estimated size in tokens when loaded into context.
   * Enables capacity feasibility [Def 3.3, condition A1] and thrashing [Prop 2.8].
   * Prefer over-estimation. Model-dependent — approximate is fine.
   */
  estimatedTokens: TokenCount,
  kind: z.enum([
    "source-file", "config-file", "sql-migration", "test-file",
    "documentation", "infrastructure", "external-service",
  ]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 2  PLAN METADATA  [FM §3.1 — Plan versioning]
// ─────────────────────────────────────────────────────────────────────────────

const PlanSupersedes = z.object({
  ref: z.string().min(1),
  deprecationHeader: z.string().optional(),
});

/**
 * [Def 3.2] Plan version transition.
 * Conditions: (1) authorized by superior, (2) re-validated, (3) traceable.
 */
const PlanVersionTransition = z.object({
  toVersion: SemVer,
  fromVersion: SemVer,
  timestamp: Timestamp,
  /** Actor authorizing the transition; must outrank `requestedBy` and cannot self-authorize [Def 3.2.1, Ax 2.4]. */
  authorizedBy: ActorId,
  requestedBy: ActorId,
  justification: z.string().min(1),
  diffSummary: z.string().min(1),
  /** Record whether well-formedness checks were rerun after the transition [Def 3.2.2]. */
  revalidated: z.boolean(),
});

const PlanMetadata = z.object({
  planId: z.string().min(1),
  version: SemVer,
  createdAt: Timestamp,
  updatedAt: Timestamp,
  authorId: ActorId,
  snapshotRef: GitSha,
  branch: z.string().min(1),
  supersedes: z.array(PlanSupersedes).default([]),
  selfPath: z.string().min(1),
  /** [Def 3.2] Version history Π_0, Π_1, ..., Π_k with authorization proof. */
  versionHistory: z.array(PlanVersionTransition).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 3  PROBLEM DEFINITION
// ─────────────────────────────────────────────────────────────────────────────

const ProblemDefinition = z.object({
  problemStatement: z.string().min(1),
  affectedActors: z.array(z.string().min(1)).min(1),
  successOutcome: z.string().min(1),
  costOfInaction: z.string().optional(),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 4  BASELINE STATE
// ─────────────────────────────────────────────────────────────────────────────

const MetricThreshold = z.object({
  name: z.string().min(1),
  baseline: z.number(),
  floor: z.number(),
  target: z.number().optional(),
  unit: z.string().min(1),
});

const BaselineState = z.object({
  snapshotRef: GitSha,
  metrics: z.array(MetricThreshold).min(1),
  knownIssues: z.array(z.string().min(1)).default([]),
  invariants: z.array(z.string().min(1)).default([]),
  healthCommands: z.array(ShellCommand).min(1),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 5  SCOPE  [FM §2.3]
// ─────────────────────────────────────────────────────────────────────────────

const ScopeZone = z.object({
  id: ScopeZoneId,
  label: z.string().min(1),
  includes: z.array(GlobPattern).min(1),
  excludes: z.array(GlobPattern).default([]),
});

const ScopeDefinition = z.object({
  inScope: z.array(ScopeZone).min(1),
  nonScope: z.array(ScopeZone).default([]),
  nonScopeRationale: z.string().optional(),
  sharedSurfaces: z.array(z.object({
    path: GlobPattern,
    reason: z.string().min(1),
    touchedBySteps: z.array(StepId).min(1),
  })).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 6  ACTOR REGISTRY  [FM §1.2 — Actor property vector]
//
// a = ⟨κ_a, τ_a, σ_a, μ_a, φ_a⟩
// ─────────────────────────────────────────────────────────────────────────────

const ActorKind = z.enum(["human", "agent", "sub-agent"]);
const ActorTrustLevel = z.enum(["operator", "orchestrator", "worker"]);

/** τ_a — Lifespan [Def 1.3]. */
const ActorLifespan = z.discriminatedUnion("kind", [
  z.object({
    kind: z.literal("unbounded"),
    /** Human memory decay profile [Def 2.6]. Qualitative — f_a is uncalibrated [§5.1.3]. */
    memoryDecayProfile: z.enum(["excellent", "moderate", "poor"]).default("moderate"),
  }),
  z.object({
    kind: z.literal("session-bounded"),
    estimatedDurationMinutes: z.number().positive().optional(),
  }),
  z.object({
    kind: z.literal("task-bounded"),
    boundToStep: StepId.optional(),
  }),
]);

/** ctx(o) = ⟨x, θ_a, seed, v_model⟩ [Def 2.13]. */
const ReproducibilityContext = z.object({
  modelVersion: z.string().min(1),
  contextHash: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  samplingParams: z.record(z.string(), z.unknown()).optional(),
});

const ActorRegistration = z.object({
  id: ActorId,
  kind: ActorKind,
  trustLevel: ActorTrustLevel,
  label: z.string().min(1),
  gitAuthor: z.string().min(1),
  /** σ(a) — authorized resource zones [Def 2.7]. */
  authorizedZones: z.array(ScopeZoneId).min(1),
  /** κ_a — context capacity [Def 1.2]. Tokens for agents, rough estimate for humans. */
  contextCapacity: TokenCount.optional(),
  /** τ_a — lifespan model [Def 1.3]. */
  lifespan: ActorLifespan.optional(),
  /**
   * φ_a(x) — output divergence [Def 2.12].
   * P(o1 ≠ o2 | same input). 0 = deterministic, 1 = max non-determinism.
   * "Right quantity to define but not practical for runtime" [§5.1.4].
   */
  outputDivergence: z.number().min(0).max(1).optional(),
  /** [Def 2.13] Full reproducibility context for AI actors. */
  reproducibility: ReproducibilityContext.optional(),
  /**
   * K_tacit [Def 2.9] — knowledge NOT in any artifact.
   * For agents: should be empty (K_a ⊆ K_explicit).
   * For humans: makes knowledge asymmetry visible.
   */
  tacitKnowledge: z.array(z.string().min(1)).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 7  COMMUNICATION CHANNELS  [FM §2.5]
//
// bw(c) = (bw_emit, bw_verify)  [Def 2.10]
// coord(Σ) ≤ min_critical min(bw_emit, bw_verify)  [Prop 2.4]
// ─────────────────────────────────────────────────────────────────────────────

const BandwidthLevel = z.enum(["very-high", "high", "medium", "low", "very-low"]);

const ChannelBandwidth = z.object({
  emit: BandwidthLevel,
  verify: BandwidthLevel,
});

const CommunicationChannel = z.object({
  from: ActorId,
  to: ActorId,
  channelType: z.enum([
    "prompt", "agent-output", "spawn-context", "peer-artifact", "human-conversation",
  ]),
  carries: z.array(z.string().min(1)).min(1),
  bandwidth: ChannelBandwidth,
  loss: z.object({
    mechanism: z.string().min(1),
    severity: z.enum(["critical", "high", "medium", "low", "negligible"]),
  }).optional(),
  /** Is this on the critical path? [Prop 2.4]. */
  onCriticalPath: z.boolean().default(false),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 8  CONCURRENCY MODEL
// ─────────────────────────────────────────────────────────────────────────────

const ConcurrencyMode = z.discriminatedUnion("mode", [
  z.object({
    mode: z.literal("sequential"),
    executorId: ActorId,
  }),
  z.object({
    mode: z.literal("parallel"),
    syncInterval: z.union([
      z.object({ kind: z.literal("per-step") }),
      z.object({ kind: z.literal("time-based"), intervalMinutes: z.number().positive() }),
    ]),
    lockProtocol: z.enum(["file-lock", "registry-lock", "branch-per-actor", "none"]),
    conflictResolution: z.enum(["halt-and-escalate", "last-write-wins", "rebase-and-revalidate"]),
  }),
]);

const ConcurrencyModel = z.object({
  mode: ConcurrencyMode,
  channels: z.array(CommunicationChannel).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 8.1  INTENT PROJECTION & VERIFICATION ECONOMICS  [FM §4.4, §4.8]
//
// Def 4.4   Intent projection          𝒢 = {(T_i, g_i)}
// Def 4.14  Bandwidth allocation       bw_decl + bw_review ≤ bw_verify
// Def 4.17  Verification viability     bw_emit,res ≤ bw_review
// ─────────────────────────────────────────────────────────────────────────────

const TemporalScope = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("all-steps") }),
  z.object({ kind: z.literal("single-step"), stepId: StepId }),
  z.object({ kind: z.literal("step-set"), stepIds: z.array(StepId).min(1) }),
  z.object({ kind: z.literal("phase"), fromStep: StepId, toStep: StepId }),
  z.object({ kind: z.literal("recurring"), everyN: z.number().int().positive() }),
]);

const IntentConstraint = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  temporalScope: TemporalScope,
  /** Def 4.18 formal modality. */
  modality: z.enum(["mathematical", "structural", "visual", "textual", "hybrid"]).default("hybrid"),
  /** Def 4.4 grading function kind. */
  gradingKind: z.enum(["boolean", "graded"]).default("boolean"),
  /** Human-readable or machine-resolvable predicate definition reference. */
  predicateRef: z.string().min(1),
  /** Def 4.15 declaration cost proxy (effort units). */
  declarationCost: z.number().nonnegative().default(0),
  /** Def 4.16 estimated verification yield proxy (dimensionless). */
  estimatedYield: z.number().nonnegative().optional(),
  notes: z.string().optional(),
});

const VerificationEconomics = z.object({
  unit: z.enum(["tokens-per-hour", "checks-per-hour", "review-points-per-hour"]).default("checks-per-hour"),
  /** Def 4.14: available verification bandwidth (upper envelope). */
  bwVerify: z.number().nonnegative(),
  /** Def 4.14: declaration allocation. */
  bwDecl: z.number().nonnegative(),
  /** Def 4.14: review allocation. */
  bwReview: z.number().nonnegative(),
  /** Def 4.17 residual emission estimate. */
  bwEmitResidual: z.number().nonnegative().optional(),
  /** Def 4.4: finite set of grounded constraints. */
  intentProjection: z.array(IntentConstraint).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 9  STEPS  [FM §3 — Plan as formal object]
// ─────────────────────────────────────────────────────────────────────────────

const StepSize = z.enum(["XS", "S", "M", "L", "XL"]);

/** [Ax 2.3]: ¬reversible(m) ⟹ gate_H(m). */
const Reversibility = z.discriminatedUnion("kind", [
  z.object({
    kind: z.literal("reversible"),
    rollbackProcedure: z.string().min(1),
  }),
  z.object({
    kind: z.literal("irreversible"),
    reason: z.string().min(1),
    mitigation: z.string().min(1),
    /** [Ax 2.3] Human gate — must be operator-level. */
    requiredApprover: ActorId,
  }),
  z.object({
    kind: z.literal("partially-reversible"),
    reversiblePart: z.string().min(1),
    irreversiblePart: z.string().min(1),
    rollbackProcedure: z.string().min(1),
    mitigation: z.string().min(1),
    /** [Ax 2.3] Human gate for irreversible portion. */
    requiredApprover: ActorId,
  }),
]);

/**
 * SAC [Def 2.17 revised] — operates on Ŝ_a(t), not S(t).
 * Every SAC has false-negative risk [Prop 2.7].
 */
const StopCondition = z.object({
  trigger: z.string().min(1),
  action: z.enum([
    "halt-and-escalate", "retry-once", "retry-with-backoff",
    "skip-and-document", "rollback-step", "rollback-all",
  ]),
  escalateTo: ActorId.optional(),
  maxRetries: z.number().int().nonnegative().default(0),
  /**
   * [Prop 2.7] What in S(t) \ Ŝ_a(t) could contain the trigger?
   * Forces acknowledgment of the blind spot paradox. "unknown" is honest.
   */
  blindSpotRisk: z.string().min(1).default("unknown"),
  /** [Cor 2.7.1] Other actors evaluating overlapping SACs for defense in depth. */
  redundantMonitors: z.array(ActorId).default([]),
});

/** Verification check with detection adequacy [Prop 2.6]. */
const VerificationCheck = z.object({
  name: z.string().min(1),
  command: ShellCommand,
  passCriteria: z.string().min(1),
  blocking: z.boolean().default(true),
  /**
   * [Prop 2.6] P[p detects error] depends on verifier's domain knowledge.
   * "self" has lowest detection (no new perspective).
   */
  verifiedBy: z.enum(["automated", "self", "peer-agent", "human"]).default("automated"),
  /** What error classes this check CAN detect. */
  detectsScope: z.string().optional(),
  /** What error classes this check CANNOT detect [Def 3.3, condition C7]. */
  cannotDetect: z.string().optional(),
});

const FileChange = z.object({
  path: z.string().min(1),
  action: z.enum(["create", "modify", "delete", "move"]),
  destination: z.string().optional(),
  description: z.string().min(1),
  resourceId: ResourceId.optional(),
});

/**
 * Blast radius [Def 2.8]: dep(r) = dep_static(r) ∪ dep_runtime(r).
 * Static-only estimate is a LOWER BOUND on β(m).
 */
const BlastRadiusEntry = z.object({
  path: GlobPattern,
  impactDescription: z.string().min(1),
  /** [Def 2.8] static = computable, runtime = not computable a priori. */
  dependencyKind: z.enum(["static", "runtime", "unknown"]).default("unknown"),
});

/** Handoff with compression loss [Def 2.5]. */
const HandoffState = z.object({
  completedSummary: z.string().min(1),
  resumptionContext: z.string().min(1),
  filesOfInterest: z.array(z.string().min(1)).default([]),
  openQuestions: z.array(z.string().min(1)).default([]),
  blockers: z.array(z.string().min(1)).default([]),
  /**
   * L(a→a') [Def 2.5]. Fraction of knowledge lost. 0=lossless, 1=amnesia.
   * Cumulative: L_cumul = 1 - ∏(1 - L_i) [Prop 2.2].
   */
  estimatedCompressionLoss: z.number().min(0).max(1).optional(),
});

/** Resource requirements for capacity feasibility [Def 3.3, condition A1] and thrashing [Prop 2.8]. */
const StepResourceRequirements = z.object({
  /** Resources needed simultaneously. Σ|r_i| must ≤ κ_a [Ax 2.1]. */
  simultaneousResources: z.array(ResourceId).default([]),
  /** Resources needed sequentially (load/unload acceptable). */
  sequentialResources: z.array(ResourceId).default([]),
  /** Token budget for reasoning beyond resource loading. */
  estimatedReasoningTokens: TokenCount.optional(),
});

/** Legacy v0.2.0 validation accounting. */
const ValidationBudgetV020 = z.object({
  required: z.number().int().nonnegative(),
  performed: z.number().int().nonnegative().default(0),
});

/**
 * v0.3.0 notation (Def 4.2 and §4.8.4):
 * val_req, val_done, val_auto, val_human, val_res
 */
const ValidationBudgetV030 = z.object({
  valReq: z.number().int().nonnegative(),
  valDone: z.number().int().nonnegative().default(0),
  valAuto: z.number().int().nonnegative().optional(),
  valHuman: z.number().int().nonnegative().optional(),
  valRes: z.number().int().nonnegative().optional(),
}).superRefine((v, ctx) => {
  if (v.valDone > v.valReq) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "valDone cannot exceed valReq",
      path: ["valDone"],
    });
  }
  if (v.valAuto != null && v.valHuman != null) {
    if (v.valAuto + v.valHuman !== v.valDone) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "valDone must equal valAuto + valHuman when both are provided",
        path: ["valDone"],
      });
    }
    if (v.valRes != null) {
      const expected = Math.max(0, v.valReq - v.valAuto);
      if (v.valRes !== expected) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `valRes should equal max(0, valReq - valAuto) = ${expected}`,
          path: ["valRes"],
        });
      }
    }
  }
});

const ValidationBudget = z.union([ValidationBudgetV030, ValidationBudgetV020]);

const PlanStep = z.object({
  id: StepId,
  title: z.string().min(1),
  description: z.string().min(1),
  size: StepSize,
  assignedTo: ActorId,
  dependsOn: z.array(StepId).default([]),
  scopeZones: z.array(ScopeZoneId).min(1),
  fileChanges: z.array(FileChange).min(1),
  blastRadius: z.array(BlastRadiusEntry).default([]),
  verification: z.array(VerificationCheck).min(1),
  reversibility: Reversibility,
  stopConditions: z.array(StopCondition).default([]),
  handoffTemplate: HandoffState.optional(),
  resourceRequirements: StepResourceRequirements.optional(),
  commitTemplate: z.string().min(1).optional(),
  notes: z.string().optional(),
  /**
   * Constraint debt tracking [Def 4.2].
   * v0.3.0 notation:
   * D(t) = Σ [val_req - val_done]^+
   * Legacy v0.2.0 fields retained for compatibility.
   */
  validationBudget: ValidationBudget.optional(),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 10-16  SUPPORTING STRUCTURES (Risk, Decision, Sync, Criteria, etc.)
// ─────────────────────────────────────────────────────────────────────────────

const Risk = z.object({
  id: RiskId,
  description: z.string().min(1),
  severity: z.enum(["critical", "high", "medium", "low"]),
  likelihood: z.enum(["almost-certain", "likely", "possible", "unlikely", "rare"]),
  affectedSteps: z.array(StepId).min(1),
  mitigation: z.string().min(1),
  fallback: z.string().optional(),
  ownerId: ActorId,
  /** Which formal constraint is under pressure [FM §2]. */
  relatedConstraint: z.enum([
    "context-capacity", "temporal-fragility", "scope-boundary",
    "knowledge-asymmetry", "communication-bandwidth", "non-determinism",
    "error-propagation", "trust-authority", "context-thrashing",
    "verification-gap", "constraint-debt", "semantic-residual",
    "specification-oversight-tradeoff", "other",
  ]).optional(),
});

const Decision = z.object({
  id: DecisionId,
  timestamp: Timestamp,
  decidedBy: ActorId,
  title: z.string().min(1),
  chosen: z.string().min(1),
  alternatives: z.array(z.object({
    option: z.string().min(1),
    rejectionReason: z.string().min(1),
  })).default([]),
  reversible: z.boolean(),
  affectedSteps: z.array(StepId).default([]),
});

const SyncRule = z.object({
  sourceOfTruth: z.array(z.string().min(1)).min(1),
  derivedArtifacts: z.array(z.string().min(1)).min(1),
  regenerateCommand: ShellCommand,
  trigger: z.union([
    z.object({ kind: z.literal("after-every-step") }),
    z.object({ kind: z.literal("after-steps"), stepIds: z.array(StepId).min(1) }),
    z.object({ kind: z.literal("manual"), instruction: z.string().min(1) }),
  ]),
});

const MigrationPolicy = z.object({
  migrationFiles: z.array(z.string().min(1)).default([]),
  idempotent: z.boolean(),
  applicationMechanism: z.string().min(1),
  failurePolicy: z.string().min(1),
});

const DataSyncRules = z.object({
  syncRules: z.array(SyncRule).default([]),
  migrationPolicy: MigrationPolicy.optional(),
});

const AcceptanceCriterion = z.object({
  description: z.string().min(1),
  verificationCommand: ShellCommand.optional(),
  passCriteria: z.string().min(1),
});

const ExecutionOrder = z.object({
  sequence: z.array(StepId).min(1),
  parallelizableGroups: z.array(z.array(StepId).min(2)).default([]),
});

const MergeStrategy = z.object({
  targetBranch: z.string().min(1),
  method: z.enum(["merge-commit", "squash", "rebase", "fast-forward"]),
  requiredGates: z.array(z.string().min(1)).min(1),
  approvers: z.array(ActorId).min(1),
});

const FutureWorkItem = z.object({
  title: z.string().min(1),
  description: z.string().min(1),
  dependsOnDecisions: z.array(DecisionId).default([]),
  targetPhase: z.string().optional(),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 17  THE PLAN  [Def 3.1: Π = ⟨G, λ, σ, γ, SAC⟩]
// ─────────────────────────────────────────────────────────────────────────────

/** Define the PlanSchema validation schema. */
export const PlanSchema = z.object({
  schemaVersion: z.literal("0.3.0"),
  metadata: PlanMetadata,
  problem: ProblemDefinition,
  baseline: BaselineState,
  /** R — resource registry [Def 1.1]. */
  resources: z.array(Resource).default([]),
  scope: ScopeDefinition,
  actors: z.array(ActorRegistration).min(1),
  concurrency: ConcurrencyModel,
  /** Def 3.3 (condition C8), Def 4.4, Def 4.14, Def 4.17 */
  verificationEconomics: VerificationEconomics.optional(),
  steps: z.array(PlanStep).min(1),
  executionOrder: ExecutionOrder,
  risks: z.array(Risk).default([]),
  decisions: z.array(Decision).default([]),
  dataSyncRules: DataSyncRules,
  acceptanceCriteria: z.array(AcceptanceCriterion).min(1),
  mergeStrategy: MergeStrategy,
  futureWork: z.array(FutureWorkItem).default([]),
});

// ─────────────────────────────────────────────────────────────────────────────
// § 18  INFERRED TYPES
// ─────────────────────────────────────────────────────────────────────────────

/** Represent Plan values inferred from the schema layer. */
export type Plan = z.infer<typeof PlanSchema>;
/** Represent PlanInput values inferred from the schema layer. */
export type PlanInput = z.input<typeof PlanSchema>;
/** Re-export branded identifier types used throughout the plan schema. */
export type { ActorId, StepId, RiskId, DecisionId, ScopeZoneId, ResourceId };
/** Represent PlanMetadata values inferred from the schema layer. */
export type PlanMetadata = z.infer<typeof PlanMetadata>;
/** Represent PlanVersionTransition values inferred from the schema layer. */
export type PlanVersionTransition = z.infer<typeof PlanVersionTransition>;
/** Represent ProblemDefinition values inferred from the schema layer. */
export type ProblemDefinition = z.infer<typeof ProblemDefinition>;
/** Represent Resource values inferred from the schema layer. */
export type Resource = z.infer<typeof Resource>;
/** Represent BaselineState values inferred from the schema layer. */
export type BaselineState = z.infer<typeof BaselineState>;
/** Represent MetricThreshold values inferred from the schema layer. */
export type MetricThreshold = z.infer<typeof MetricThreshold>;
/** Represent ScopeDefinition values inferred from the schema layer. */
export type ScopeDefinition = z.infer<typeof ScopeDefinition>;
/** Represent ScopeZone values inferred from the schema layer. */
export type ScopeZone = z.infer<typeof ScopeZone>;
/** Represent ActorRegistration values inferred from the schema layer. */
export type ActorRegistration = z.infer<typeof ActorRegistration>;
/** Represent ActorLifespan values inferred from the schema layer. */
export type ActorLifespan = z.infer<typeof ActorLifespan>;
/** Represent ReproducibilityContext values inferred from the schema layer. */
export type ReproducibilityContext = z.infer<typeof ReproducibilityContext>;
/** Represent CommunicationChannel values inferred from the schema layer. */
export type CommunicationChannel = z.infer<typeof CommunicationChannel>;
/** Represent ChannelBandwidth values inferred from the schema layer. */
export type ChannelBandwidth = z.infer<typeof ChannelBandwidth>;
/** Represent ConcurrencyModel values inferred from the schema layer. */
export type ConcurrencyModel = z.infer<typeof ConcurrencyModel>;
/** Represent TemporalScope values inferred from the schema layer. */
export type TemporalScope = z.infer<typeof TemporalScope>;
/** Represent IntentConstraint values inferred from the schema layer. */
export type IntentConstraint = z.infer<typeof IntentConstraint>;
/** Represent VerificationEconomics values inferred from the schema layer. */
export type VerificationEconomics = z.infer<typeof VerificationEconomics>;
/** Represent PlanStep values inferred from the schema layer. */
export type PlanStep = z.infer<typeof PlanStep>;
/** Represent ValidationBudget values inferred from the schema layer. */
export type ValidationBudget = z.infer<typeof ValidationBudget>;
/** Represent StepResourceRequirements values inferred from the schema layer. */
export type StepResourceRequirements = z.infer<typeof StepResourceRequirements>;
/** Represent FileChange values inferred from the schema layer. */
export type FileChange = z.infer<typeof FileChange>;
/** Represent BlastRadiusEntry values inferred from the schema layer. */
export type BlastRadiusEntry = z.infer<typeof BlastRadiusEntry>;
/** Represent VerificationCheck values inferred from the schema layer. */
export type VerificationCheck = z.infer<typeof VerificationCheck>;
/** Represent Reversibility values inferred from the schema layer. */
export type Reversibility = z.infer<typeof Reversibility>;
/** Represent StopCondition values inferred from the schema layer. */
export type StopCondition = z.infer<typeof StopCondition>;
/** Represent HandoffState values inferred from the schema layer. */
export type HandoffState = z.infer<typeof HandoffState>;
/** Represent Risk values inferred from the schema layer. */
export type Risk = z.infer<typeof Risk>;
/** Represent Decision values inferred from the schema layer. */
export type Decision = z.infer<typeof Decision>;
/** Represent SyncRule values inferred from the schema layer. */
export type SyncRule = z.infer<typeof SyncRule>;
/** Represent MigrationPolicy values inferred from the schema layer. */
export type MigrationPolicy = z.infer<typeof MigrationPolicy>;
/** Represent DataSyncRules values inferred from the schema layer. */
export type DataSyncRules = z.infer<typeof DataSyncRules>;
/** Represent AcceptanceCriterion values inferred from the schema layer. */
export type AcceptanceCriterion = z.infer<typeof AcceptanceCriterion>;
/** Represent MergeStrategy values inferred from the schema layer. */
export type MergeStrategy = z.infer<typeof MergeStrategy>;
/** Represent FutureWorkItem values inferred from the schema layer. */
export type FutureWorkItem = z.infer<typeof FutureWorkItem>;
/** Represent ExecutionOrder values inferred from the schema layer. */
export type ExecutionOrder = z.infer<typeof ExecutionOrder>;

// ─────────────────────────────────────────────────────────────────────────────
// § 19  WELL-FORMEDNESS VALIDATION  [Def 3.3 — 8 conditions]
// ─────────────────────────────────────────────────────────────────────────────

/** Define the WellFormednessResult interface contract. */
export interface WellFormednessResult {
  /**
   * Hard violations of model constraints.
   * Execution policy: block and escalate until resolved.
   */
  errors: string[];
  /**
   * Risk signals and debt pressure.
   * Execution policy: continue only with explicit mitigation/acceptance.
   */
  warnings: string[];
}

function normalizeValidationBudget(
  budget: z.infer<typeof ValidationBudget>
): { valReq: number; valDone: number; valAuto?: number; valHuman?: number; valRes?: number } {
  if ("valReq" in budget) {
    return {
      valReq: budget.valReq,
      valDone: budget.valDone,
      valAuto: budget.valAuto,
      valHuman: budget.valHuman,
      valRes: budget.valRes,
    };
  }
  return {
    valReq: budget.required,
    valDone: budget.performed,
  };
}

/**
 * Validate structural and governance constraints for a plan instance.
 *
 * @param plan - Parsed plan document to validate.
 * @returns Hard errors and warning signals discovered by well-formedness checks.
 */
export function validateWellFormedness(plan: Plan): WellFormednessResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const actorIds = new Set(plan.actors.map((a) => a.id));
  const actorMap = new Map(plan.actors.map((a) => [a.id, a]));
  const stepIds = new Set(plan.steps.map((s) => s.id));
  const resourceMap = new Map(plan.resources.map((r) => [r.id, r]));
  const inScopeZoneIds = new Set(plan.scope.inScope.map((sz) => sz.id));

  // ── 1. Referential integrity ──

  for (const step of plan.steps) {
    if (!actorIds.has(step.assignedTo)) {
      errors.push(`Step "${step.id}" assigned to unregistered actor "${step.assignedTo}"`);
    }
    for (const zid of step.scopeZones) {
      if (!inScopeZoneIds.has(zid)) {
        errors.push(`Step "${step.id}" references scope zone "${zid}" not in inScope`);
      }
    }
    for (const depId of step.dependsOn) {
      if (!stepIds.has(depId)) errors.push(`Step "${step.id}" depends on nonexistent step "${depId}"`);
      if (depId === step.id) errors.push(`Step "${step.id}" depends on itself`);
    }
  }

  for (const risk of plan.risks) {
    if (!actorIds.has(risk.ownerId)) errors.push(`Risk "${risk.id}" owned by unregistered actor "${risk.ownerId}"`);
    for (const sid of risk.affectedSteps) {
      if (!stepIds.has(sid)) errors.push(`Risk "${risk.id}" references nonexistent step "${sid}"`);
    }
  }

  for (const dec of plan.decisions) {
    if (!actorIds.has(dec.decidedBy)) errors.push(`Decision "${dec.id}" by unregistered actor "${dec.decidedBy}"`);
    for (const sid of dec.affectedSteps) {
      if (!stepIds.has(sid)) errors.push(`Decision "${dec.id}" references nonexistent step "${sid}"`);
    }
  }

  for (const surf of plan.scope.sharedSurfaces) {
    for (const sid of surf.touchedBySteps) {
      if (!stepIds.has(sid)) errors.push(`Shared surface "${surf.path}" references nonexistent step "${sid}"`);
    }
  }

  for (const aid of plan.mergeStrategy.approvers) {
    if (!actorIds.has(aid)) errors.push(`Merge approver "${aid}" not registered`);
  }

  if (plan.metadata.snapshotRef !== plan.baseline.snapshotRef) {
    errors.push(`Metadata snapshotRef (${plan.metadata.snapshotRef}) ≠ baseline snapshotRef (${plan.baseline.snapshotRef})`);
  }

  // ── 2. Scope containment [Ax 2.2] ──

  for (const step of plan.steps) {
    const actor = actorMap.get(step.assignedTo);
    if (actor) {
      for (const zid of step.scopeZones) {
        if (!actor.authorizedZones.includes(zid)) {
          errors.push(`[Ax 2.2] Step "${step.id}" uses zone "${zid}" but actor "${actor.id}" is not authorized`);
        }
      }
    }
  }

  // ── 3. DAG acyclicity [Def 3.1] ──

  const inDeg = new Map<string, number>();
  const adj = new Map<string, string[]>();
  for (const step of plan.steps) {
    inDeg.set(step.id, step.dependsOn.length);
    for (const depId of step.dependsOn) {
      const list = adj.get(depId) ?? [];
      list.push(step.id);
      adj.set(depId, list);
    }
  }
  const queue: string[] = [];
  for (const [id, deg] of inDeg) { if (deg === 0) queue.push(id); }
  let visited = 0;
  while (queue.length > 0) {
    const cur = queue.shift()!;
    visited++;
    for (const nb of adj.get(cur) ?? []) {
      const nd = (inDeg.get(nb) ?? 0) - 1;
      inDeg.set(nb, nd);
      if (nd === 0) queue.push(nb);
    }
  }
  if (visited !== plan.steps.length) errors.push("Step dependency graph contains a cycle [Def 3.1]");

  // ── 4. Execution order completeness ──

  const seqSet = new Set(plan.executionOrder.sequence);
  for (const sid of stepIds) { if (!seqSet.has(sid)) errors.push(`Step "${sid}" not in executionOrder.sequence`); }
  for (const sid of plan.executionOrder.sequence) { if (!stepIds.has(sid)) errors.push(`executionOrder references nonexistent step "${sid}"`); }

  // ── 5. Capacity feasibility [Def 3.3, condition A1] + thrashing [Prop 2.8] ──

  for (const step of plan.steps) {
    const reqs = step.resourceRequirements;
    const actor = actorMap.get(step.assignedTo);
    if (reqs && actor?.contextCapacity) {
      let simTokens = 0;
      for (const rid of reqs.simultaneousResources) {
        const r = resourceMap.get(rid);
        if (r) simTokens += r.estimatedTokens;
        else warnings.push(`Step "${step.id}" references unregistered resource "${rid}"`);
      }
      const total = simTokens + (reqs.estimatedReasoningTokens ?? 0);
      if (total > actor.contextCapacity) {
        errors.push(
          `[Def 3.3/A1] Step "${step.id}" requires ~${total} tokens but actor "${actor.id}" capacity is ${actor.contextCapacity}. Infeasible [Prop 2.8].`
        );
      } else if (total > actor.contextCapacity * 0.8) {
        warnings.push(`Step "${step.id}" uses ~${Math.round(total / actor.contextCapacity * 100)}% of capacity — thrashing risk [Def 2.19].`);
      }
    }
  }

  // ── 6. Irreversibility gating [Ax 2.3] ──

  for (const step of plan.steps) {
    if (step.reversibility.kind === "irreversible" || step.reversibility.kind === "partially-reversible") {
      const appId = step.reversibility.requiredApprover;
      const approver = actorMap.get(appId);
      if (!approver) {
        errors.push(`[Ax 2.3] Step "${step.id}" is ${step.reversibility.kind} but approver "${appId}" not registered`);
      } else if (approver.trustLevel !== "operator") {
        errors.push(`[Ax 2.3] Step "${step.id}" is ${step.reversibility.kind} but approver "${appId}" is "${approver.trustLevel}", not "operator"`);
      }
      if (appId === step.assignedTo) {
        errors.push(`[Ax 2.4] Step "${step.id}": executor cannot self-approve irreversible action`);
      }
    }
  }

  // ── 7. Detection adequacy [Def 3.3, condition C7] ──

  for (const step of plan.steps) {
    if (step.verification.every((v) => v.verifiedBy === "self")) {
      warnings.push(`[Prop 2.6] Step "${step.id}" has only self-verification — low detection capacity.`);
    }
  }

  // ── 8. Intent projection adequacy [Def 3.3, condition C8 + Def 4.14/4.17] ──

  if (!plan.verificationEconomics) {
    errors.push("[Def 3.3/C8] Missing verificationEconomics: cannot establish intent-projection adequacy.");
  } else {
    const ve = plan.verificationEconomics;
    if (ve.intentProjection.length === 0) {
      errors.push("[Def 3.3/C8] intentProjection is empty: no grounded constraints declared.");
    }
    if (ve.bwDecl + ve.bwReview > ve.bwVerify) {
      errors.push(
        `[Def 4.14] bwDecl + bwReview = ${ve.bwDecl + ve.bwReview} exceeds bwVerify = ${ve.bwVerify}.`
      );
    }
    if (ve.bwEmitResidual != null && ve.bwEmitResidual > ve.bwReview) {
      warnings.push(
        `[Def 4.17] bwEmitResidual (${ve.bwEmitResidual}) > bwReview (${ve.bwReview}): verification viability at risk.`
      );
    }

    for (const c of ve.intentProjection) {
      if (c.temporalScope.kind === "single-step" && !stepIds.has(c.temporalScope.stepId)) {
        errors.push(`Intent constraint "${c.id}" references nonexistent step "${c.temporalScope.stepId}".`);
      }
      if (c.temporalScope.kind === "step-set") {
        for (const sid of c.temporalScope.stepIds) {
          if (!stepIds.has(sid)) errors.push(`Intent constraint "${c.id}" references nonexistent step "${sid}".`);
        }
      }
      if (c.temporalScope.kind === "phase") {
        if (!stepIds.has(c.temporalScope.fromStep)) errors.push(`Intent constraint "${c.id}" references nonexistent fromStep "${c.temporalScope.fromStep}".`);
        if (!stepIds.has(c.temporalScope.toStep)) errors.push(`Intent constraint "${c.id}" references nonexistent toStep "${c.temporalScope.toStep}".`);
      }
    }
  }

  // ── 9. Plan version transition authorization [Def 3.2] ──

  for (const tr of plan.metadata.versionHistory) {
    if (tr.authorizedBy === tr.requestedBy) {
      errors.push(`[Def 3.2] Version ${tr.toVersion}: requestedBy = authorizedBy = "${tr.authorizedBy}". Cannot self-authorize [Ax 2.4].`);
    }
    const auth = actorMap.get(tr.authorizedBy);
    if (auth && auth.trustLevel === "worker") {
      errors.push(`[Def 3.2] Version ${tr.toVersion}: authorized by worker "${tr.authorizedBy}". Requires orchestrator+.`);
    }
  }

  // ── 10. Constraint debt [Def 4.2] ──

  let totalDebt = 0;
  for (const step of plan.steps) {
    if (step.validationBudget) {
      const vb = normalizeValidationBudget(step.validationBudget);
      const deficit = vb.valReq - vb.valDone;
      if (deficit > 0) {
        totalDebt += deficit;
        warnings.push(`[Def 4.2] Step "${step.id}": validation ${vb.valDone}/${vb.valReq}.`);
      }
    }
  }
  if (totalDebt > 0) {
    warnings.push(`[Def 4.2] Total constraint debt D(t) = ${totalDebt}.`);
  }

  // ── 11. Handoff compression loss accumulation [Prop 2.2] ──

  const losses = plan.steps
    .filter((s) => s.handoffTemplate?.estimatedCompressionLoss != null)
    .map((s) => s.handoffTemplate!.estimatedCompressionLoss!);
  if (losses.length > 1) {
    const cumul = 1 - losses.reduce((acc, l) => acc * (1 - l), 1);
    if (cumul > 0.5) {
      warnings.push(`[Prop 2.2] Cumulative handoff loss across ${losses.length} handoffs: ~${Math.round(cumul * 100)}%.`);
    }
  }

  // ── 12. Verification gap [Cor 4.1.1] ──

  const bwRank: Record<string, number> = { "very-low": 1, "low": 2, "medium": 3, "high": 4, "very-high": 5 };
  for (const ch of plan.concurrency.channels) {
    if (ch.onCriticalPath) {
      const emitR = bwRank[ch.bandwidth.emit] ?? 0;
      const verifyR = bwRank[ch.bandwidth.verify] ?? 0;
      if (emitR - verifyR >= 2) {
        warnings.push(`[Cor 4.1.1] Channel ${ch.from}→${ch.to}: emit(${ch.bandwidth.emit}) >> verify(${ch.bandwidth.verify}). Verification gap grows.`);
      }
    }
  }

  // ── 13. Blast radius lower bound [Def 2.8] ──

  for (const step of plan.steps) {
    const hasStatic = step.blastRadius.some((b) => b.dependencyKind === "static");
    const hasRuntime = step.blastRadius.some((b) => b.dependencyKind === "runtime" || b.dependencyKind === "unknown");
    if (hasRuntime && !hasStatic && step.blastRadius.length > 0) {
      warnings.push(`[Def 2.8] Step "${step.id}": only runtime/unknown blast radius — no static lower bound on β(m).`);
    }
  }

  return { errors, warnings };
}

/**
 * Return only hard consistency errors for backward compatibility.
 *
 * @param plan - Parsed plan document to validate.
 * @returns Array of hard consistency errors.
 */
export function validatePlanConsistency(plan: Plan): string[] {
  return validateWellFormedness(plan).errors;
}
