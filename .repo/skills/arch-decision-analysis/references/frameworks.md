# Analytical Frameworks Reference

Read this file when the decision involves complex trade-off structures that
benefit from a formal framework. Not every analysis needs all of these — pick
the frameworks that match the decision's shape.

---

## 1. Wardley Mapping (Positional Analysis)

Use when the decision involves components at different stages of maturity
(genesis → custom → product → commodity). Helps reveal:

- Whether you're building custom what should be commodity (over-engineering)
- Whether you're commoditizing what's still in genesis (premature abstraction)
- Movement patterns: which components are evolving toward commodity

**Application**: For each option, identify where it sits on the evolution axis.
Options that treat an evolving component as static will accumulate drift cost.

---

## 2. Real Options Analysis

Use when the decision involves uncertainty that will resolve over time. The key
insight: keeping options open has value, and that value can be reasoned about.

**Key questions**:
- What is the cost of keeping this option open for N more months?
- What information would arrive in N months that changes the calculus?
- Is the option premium (cost of deferral) justified by the option value
  (ability to choose better later)?

**Application**: For each option, estimate:
- Adoption cost now vs. adoption cost in 6 months
- Information that would change the decision
- Whether the option appreciates or depreciates over time

---

## 3. Cynefin Categorization

Use when the decision's complexity level is itself unclear. Categorize the
decision domain:

- **Clear**: Best practice exists. Follow it.
- **Complicated**: Expertise needed, but analysis yields a right answer.
- **Complex**: No right answer discoverable in advance. Probe, sense, respond.
- **Chaotic**: Act first, then sense and respond.

**Application**: If the decision is in the Complex domain, the recommendation
shifts from "pick the best option" to "pick the option with the fastest
feedback loop." If Chaotic, recommend the option with lowest blast radius.

---

## 4. Dependency / Coupling Analysis

Use when options create different coupling structures. Analyze:

- **Afferent coupling** (who depends on this): Higher = more expensive to change
- **Efferent coupling** (what this depends on): Higher = more fragile
- **Stability metric**: Afferent / (Afferent + Efferent). Stable components
  should be abstract; unstable ones should be concrete.

**Application**: For each option, sketch the dependency graph. Options that
create high afferent coupling for volatile components are architecturally risky.

---

## 5. ATAM-Lite (Architecture Tradeoff Analysis)

Simplified version of the SEI's Architecture Tradeoff Analysis Method:

1. **Identify quality attribute scenarios**: Concrete, measurable statements
   like "Under 10k concurrent users, p99 latency stays under 200ms."
2. **Map options to scenarios**: For each option, assess which scenarios it
   satisfies, partially satisfies, or violates.
3. **Identify sensitivity points**: Places where a small change in the option
   causes a large change in quality attribute response.
4. **Identify tradeoff points**: Places where improving one quality attribute
   necessarily degrades another.

**Application**: The sensitivity and tradeoff points are the real output —
they show where the decision actually matters vs. where it's noise.

---

## 6. Composition Algebra

For analyzing whether options combine:

- **Additive composition**: A + B gives benefits of both with minimal
  interaction cost. (e.g., caching + CDN)
- **Multiplicative composition**: A × B amplifies both. (e.g., type safety +
  automated testing)
- **Subtractive composition**: A - B where one partially cancels the other.
  (e.g., adding a cache when the bottleneck is compute, not I/O)
- **Conflicting composition**: A ⊕ B where both cannot coexist.
  (e.g., two ORMs in the same data layer)

**Application**: Build the composition matrix from Phase 3d using these
categories. Identify the highest-value additive and multiplicative pairs.

---

## 7. Reversibility Taxonomy

Classify each option's reversibility:

| Type | Description | Example |
|------|-------------|---------|
| **Type 1** | Fully reversible, low cost | Feature flag toggle |
| **Type 2** | Reversible with data migration | Database schema change |
| **Type 3** | Reversible with rewrite | Framework swap |
| **Type 4** | Irreversible (practically) | Public API contract |

**Application**: Map each option to a reversibility type. Type 1-2 decisions
can be made quickly. Type 3-4 decisions deserve the full analysis treatment.

---

## 8. Gain/Loss Space Matrix

For structured comparison across evaluation axes:

```
           Axis 1    Axis 2    Axis 3    Axis 4
Option A   [score]   [score]   [score]   [score]
Option B   [score]   [score]   [score]   [score]
Option C   [score]   [score]   [score]   [score]
```

Scoring is relative to the current state (the "do nothing" baseline):
- **++** : Significant improvement
- **+**  : Moderate improvement
- **0**  : No change
- **-**  : Moderate degradation
- **--** : Significant degradation
- **?**  : Unknown / depends on implementation

**Application**: Generate this matrix, then look for:
- Pareto-dominated options (some option is worse on every axis — eliminate it)
- Pareto-optimal frontier (options that are best on at least one axis)
- The shape of the frontier reveals the fundamental trade-off structure
