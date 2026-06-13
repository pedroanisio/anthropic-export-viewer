# Example Experiment: Most Realistic 3D Femur

This walkthrough demonstrates the full experiment loop applied to the
problem: "Build the most realistic browser-rendered 3D femur bone."

## Phase 0: Definition

**Objective**: Produce a Three.js-rendered femur model that a medical
student would find anatomically plausible at first glance.

**Medium**: React artifact using Three.js (r128, available in Claude
artifact environment).

**Evaluation Dimensions**:

| ID                  | Label               | Weight | Key Question                                |
|---------------------|----------------------|--------|---------------------------------------------|
| anatomical_accuracy | Anatomical Accuracy  | 0.35   | Does it look like a real femur?             |
| surface_realism     | Surface Realism      | 0.25   | Does the bone surface look like bone?       |
| structural_detail   | Structural Detail    | 0.20   | Cortical/cancellous distinction, features?  |
| technical_quality   | Technical Quality    | 0.20   | Clean code, good performance, maintainable? |

**Success Threshold**: ≥7 on every dimension, ≥7.5 weighted average.

**Reference Material** (gather via search before starting):
- Anatomical diagrams of femur (anterior, posterior, lateral views)
- Key landmarks: femoral head, neck, greater & lesser trochanters,
  shaft, medial & lateral condyles, intercondylar fossa, linea aspera
- Proportions: head ~45mm diameter, neck-shaft angle ~125°, total
  length ~450mm, shaft diameter ~28mm
- Bone surface characteristics: ivory/cream color, slightly rough
  texture, subtle periosteal vasculature patterns

## Phase 1: Round 1 Hypotheses

### Variant A — Parametric Bone Geometry

**Hypothesis**: Modeling the femur as a sequence of parametric shapes
(sphere for head, tapered cylinder for neck, cylinder with flare for
shaft, condylar masses) with smooth transitions will produce accurate
anatomy because the femur's gross structure maps well to geometric
primitives.

**Approach**: Three.js BufferGeometry with custom vertex generation.
Define the femur as a spline-guided tube with varying cross-section
radii, then add landmark bumps procedurally.

**Predicted strengths**: Anatomical accuracy, programmatic control.
**Predicted weaknesses**: Surface too smooth and synthetic.

### Variant B — Displacement-Mapped Sphere

**Hypothesis**: A high-poly UV sphere with vertex displacement from
a procedurally generated heightmap will produce better organic surface
quality than pure geometry, because displacement maps naturally encode
the kind of irregular surface variation found in biological structures.

**Approach**: Three.js SphereGeometry (high subdivision) with a vertex
shader that displaces vertices based on a 3D noise function shaped to
approximate femoral anatomy.

**Predicted strengths**: Organic surface quality, natural irregularity.
**Predicted weaknesses**: Hard to control specific anatomical landmarks.

### Variant C — Lathe Geometry from Anatomical Profile

**Hypothesis**: The femur's silhouette from the anterior view can be
approximated as a path, and Three.js LatheGeometry can revolve this
profile to create the basic 3D shape. Post-processing can break the
rotational symmetry to add condyles and trochanters.

**Approach**: Define the femur profile as a 2D spline path. Revolve
with LatheGeometry. Add landmark geometry as merged shapes.

**Predicted strengths**: Quick, accurate silhouette.
**Predicted weaknesses**: Rotational symmetry artifacts, seams.

### Variant D — SDF Raymarching

**Hypothesis**: Signed distance functions (SDFs) can represent the femur
as a union of smooth primitives (spheres, capsules, boxes) with smooth
blending, producing both accurate anatomy and organic transitions that
mesh-based approaches struggle with.

**Approach**: Custom fragment shader rendering SDF scene. Model the
femur as ~8-10 blended SDF primitives (sphere for head, capsule for
neck, tapered capsule for shaft, etc.).

**Predicted strengths**: Smooth organic transitions, resolution-independent.
**Predicted weaknesses**: No mesh (can't use standard Three.js materials),
hard to add surface texture, computationally expensive.

## Phase 2: Execution Notes

Each variant is implemented as a standalone React component.
All use the same camera angle and lighting setup for fair comparison:
- Camera: orbiting at 45° elevation, 500mm distance
- Lighting: 3-point setup (key, fill, rim) + ambient
- Background: neutral dark gray
- Controls: OrbitControls for user interaction

Filename pattern: `experiment-femur-r1-variant-{a|b|c|d}.jsx`

## Phase 3: Expected Observations

After rendering, assess each variant against every evaluation dimension.
Pay special attention to:

- **Silhouette test**: Does the outline look right from 4+ angles?
- **Landmark count**: How many of the 8 key landmarks are visible?
- **Surface test**: Zoom in — does it look like bone or plastic?
- **Animation test**: Rotate slowly — do any artifacts appear?

## Phases 4-5: Expected Round 1 Analysis Pattern

Typical Round 1 results for this kind of experiment:

- Variant A (parametric) likely leads on anatomy, lags on surface
- Variant B (displacement) likely leads on surface, lags on anatomy
- Variant C (lathe) is likely the fastest but most limited
- Variant D (SDF) is likely the most technically interesting but
  hardest to get right in one iteration

The synthesis step should:
1. Take the best anatomical approach (probably A) as the skeleton
2. Apply the best surface approach (probably B) as a detail layer
3. Consider whether SDF's smooth blending could improve transitions
4. Drop the weakest approach unless it has a salvageable technique

## Round 2 Hypotheses (Projected)

After Round 1 analysis, Round 2 typically involves:

- **Hybrid AB**: Parametric skeleton geometry + displacement detail pass
- **Enhanced A**: Parametric with added noise perturbation for organics
- **New approach**: Procedural bone material shader applied to best geometry

## Three.js Techniques Catalog

Techniques commonly useful for organic 3D modeling in Three.js:

| Technique              | Good For                        | Complexity |
|------------------------|---------------------------------|------------|
| BufferGeometry         | Custom vertex placement         | Medium     |
| LatheGeometry          | Rotationally symmetric shapes   | Low        |
| TubeGeometry           | Spline-following shapes         | Low        |
| Vertex displacement    | Surface detail, organic feel    | Medium     |
| Custom ShaderMaterial  | Advanced lighting, SSS          | High       |
| MeshPhysicalMaterial   | PBR with roughness/metalness    | Low        |
| Normal map from noise  | Fake surface detail cheaply     | Medium     |
| Procedural 3D texture  | Non-repeating organic patterns  | High       |

**Important Three.js r128 Constraints** (artifact environment):
- THREE.CapsuleGeometry does NOT exist in r128 — use cylinder + spheres
- OrbitControls must be implemented manually (no module import)
- Textures must be generated procedurally (no external image loading)
- Max comfortable vertex count: ~50K for smooth interaction
