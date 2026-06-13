# Experiment Schema Reference

## experiment.json

Root definition for an experiment. Created during Phase 0.

```json
{
  "experiment_id": "femur-3d-realism",
  "created": "2026-04-14T12:00:00Z",
  "objective": "Produce a browser-rendered 3D femur model...",
  "medium": "threejs-react",
  "evaluation_dimensions": [
    {
      "id": "anatomical_accuracy",
      "label": "Anatomical Accuracy",
      "description": "Shape, proportions, landmark placement vs reference anatomy",
      "weight": 0.35,
      "rubric": {
        "1-3": "Unrecognizable as a femur or grossly wrong proportions",
        "4-5": "Recognizable femur shape but missing key landmarks",
        "6-7": "Good shape with most landmarks, some proportion issues",
        "8-9": "Accurate shape, proportions, and landmark placement",
        "10": "Indistinguishable from a textbook reference illustration"
      }
    }
  ],
  "references": [
    {
      "type": "image_search",
      "query": "femur bone anatomy 3D render",
      "description": "Reference images for anatomical shape"
    },
    {
      "type": "url",
      "url": "https://...",
      "description": "Medical illustration source"
    }
  ],
  "success_threshold": {
    "min_per_dimension": 7,
    "weighted_average": 7.5
  },
  "iteration_budget": {
    "max_rounds": 3,
    "variants_per_round": 4,
    "min_improvement_to_continue": 0.5
  }
}
```

## hypotheses.json

Written during Phase 1, one per round.

```json
{
  "round": 1,
  "variants": [
    {
      "id": "parametric-geometry",
      "hypothesis": "Mathematical bone shape functions can produce...",
      "approach": "Three.js BufferGeometry with parametric vertex positions",
      "predicted_strengths": ["anatomical accuracy", "control"],
      "predicted_weaknesses": ["surface realism", "organic feel"],
      "parent_variants": [],
      "evidence_basis": null
    },
    {
      "id": "displacement-sphere",
      "hypothesis": "Starting from a UV sphere with displacement...",
      "approach": "Three.js sphere + vertex shader displacement",
      "predicted_strengths": ["surface realism"],
      "predicted_weaknesses": ["anatomical landmarks"],
      "parent_variants": [],
      "evidence_basis": null
    }
  ]
}
```

For rounds > 1, `parent_variants` and `evidence_basis` reference
previous round data:

```json
{
  "id": "parametric-with-displacement",
  "parent_variants": ["round-1/parametric-geometry", "round-1/displacement-sphere"],
  "evidence_basis": "Round 1: parametric scored 8/10 anatomy, displacement scored 8/10 surface. Combining should yield ≥7 on both."
}
```

## observations.json

One per variant, written during Phase 3.

```json
{
  "variant_id": "parametric-geometry",
  "round": 1,
  "visual_assessment": {
    "overall_impression": "Clean geometric shape, clearly a femur...",
    "strengths": ["correct silhouette", "visible head and neck"],
    "weaknesses": ["too smooth", "no surface texture variation"],
    "comparison_to_reference": "Shape matches ~75%, surface 40%"
  },
  "dimension_scores": [
    {
      "dimension_id": "anatomical_accuracy",
      "score": 7,
      "justification": "All major landmarks present. Greater trochanter slightly oversized."
    },
    {
      "dimension_id": "surface_realism",
      "score": 4,
      "justification": "Uniform smooth surface. No periosteum texture, no color variation."
    }
  ],
  "programmatic_metrics": {
    "vertex_count": 2400,
    "triangle_count": 4600,
    "file_size_bytes": 18200,
    "render_fps": 60
  },
  "user_feedback": null
}
```

## comparison.json

One per round, written during Phase 4.

```json
{
  "round": 1,
  "matrix": {
    "anatomical_accuracy": { "parametric": 7, "displacement": 5, "sdf": 6 },
    "surface_realism": { "parametric": 4, "displacement": 8, "sdf": 6 },
    "weighted_totals": { "parametric": 5.9, "displacement": 6.2, "sdf": 6.0 }
  },
  "analysis": {
    "best_per_dimension": {
      "anatomical_accuracy": "parametric",
      "surface_realism": "displacement"
    },
    "hypotheses_confirmed": ["parametric-geometry", "displacement-sphere"],
    "hypotheses_refuted": [],
    "key_insight": "Parametric approach excels at structure but cannot encode organic texture. Displacement excels at surface but loses structural landmarks. Combination is the obvious next step.",
    "techniques_to_carry_forward": [
      "Parametric vertex generation for skeleton",
      "Displacement mapping for surface detail pass"
    ],
    "techniques_to_drop": []
  }
}
```

## learnings.json

Written at experiment conclusion. Distills insights for future use.

```json
{
  "experiment_id": "femur-3d-realism",
  "total_rounds": 3,
  "total_variants_tested": 10,
  "best_variant": "round-3/parametric-displacement-refined",
  "final_scores": {
    "anatomical_accuracy": 8,
    "surface_realism": 8,
    "structural_detail": 7,
    "technical_quality": 8,
    "weighted_average": 7.8
  },
  "key_learnings": [
    {
      "insight": "Two-pass approach (structure then detail) consistently outperforms single-pass",
      "evidence": "All top-3 variants used layered geometry generation",
      "generalizability": "Likely applies to any organic 3D model, not just bones"
    }
  ],
  "failed_approaches": [
    {
      "approach": "Pure SDF raymarching",
      "why_failed": "Fragment shader approach couldn't leverage Three.js lighting pipeline",
      "lesson": "Choose rendering approach compatible with the target framework's strengths"
    }
  ]
}
```
