/*
 * EXPERIMENT CONTROLLER TEMPLATE
 * 
 * This React artifact template demonstrates how to build a multi-agent
 * evaluation system using the Anthropic API. Adapt it for your experiment.
 *
 * Usage: Copy and customize for each experiment. Replace the CUSTOMIZE
 * blocks with your experiment-specific configuration.
 */

import { useState, useCallback } from "react";

// ============================================================
// CUSTOMIZE: Define your evaluation dimensions and agent prompts
// ============================================================
const DIMENSIONS = [
  {
    id: "anatomical_accuracy",
    label: "Anatomical Accuracy",
    weight: 0.35,
    agentPrompt: `You are an anatomist evaluating a 3D model for structural accuracy.
Evaluate criteria: landmark presence, proportions, silhouette correctness.
Score 1-10. Respond ONLY with JSON: {"score": N, "justification": "...", "strengths": [...], "weaknesses": [...]}`,
  },
  {
    id: "surface_realism",
    label: "Surface Realism",
    weight: 0.25,
    agentPrompt: `You are a 3D artist evaluating surface material quality.
Evaluate: light response, color variation, texture grain, specular behavior.
Score 1-10. Respond ONLY with JSON: {"score": N, "justification": "...", "strengths": [...], "weaknesses": [...]}`,
  },
  // Add more dimensions as needed
];

// ============================================================
// CUSTOMIZE: Define your variants (code or descriptions to evaluate)
// ============================================================
const VARIANTS = [
  {
    id: "variant-a",
    name: "Parametric Geometry",
    description: "Femur built from parametric shape functions...",
    // For code-based evaluation, include the code:
    code: "// paste variant code here",
  },
  // Add more variants
];

// ============================================================
// API call function
// ============================================================
async function evaluateWithAgent(variant, dimension) {
  try {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 1000,
        system: dimension.agentPrompt,
        messages: [
          {
            role: "user",
            content: `Evaluate this variant for ${dimension.label}.

VARIANT: ${variant.name}
DESCRIPTION: ${variant.description}

CODE:
\`\`\`
${variant.code || "N/A"}
\`\`\`

Score 1-10. Respond ONLY with JSON:
{"score": <number>, "justification": "<explanation>", "strengths": ["..."], "weaknesses": ["..."]}`,
          },
        ],
      }),
    });

    const data = await response.json();
    const text = data.content
      ?.filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    const clean = text.replace(/```json|```/g, "").trim();
    return JSON.parse(clean);
  } catch (err) {
    return {
      score: 0,
      justification: `Agent error: ${err.message}`,
      strengths: [],
      weaknesses: [],
    };
  }
}

// ============================================================
// Main Component
// ============================================================
export default function ExperimentController() {
  const [results, setResults] = useState({});
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });

  const runEvaluation = useCallback(async () => {
    setRunning(true);
    const total = VARIANTS.length * DIMENSIONS.length;
    setProgress({ done: 0, total });

    const allResults = {};
    let done = 0;

    for (const variant of VARIANTS) {
      allResults[variant.id] = { variant, scores: {} };

      // Run all dimension evaluations for this variant
      // (sequential to avoid rate limits, but independent)
      for (const dim of DIMENSIONS) {
        const result = await evaluateWithAgent(variant, dim);
        allResults[variant.id].scores[dim.id] = result;
        done++;
        setProgress({ done, total });
        setResults({ ...allResults });
      }
    }

    setRunning(false);
  }, []);

  // Compute weighted averages
  const computeWeightedAvg = (scores) => {
    let sum = 0;
    let weightSum = 0;
    for (const dim of DIMENSIONS) {
      const s = scores[dim.id];
      if (s && s.score > 0) {
        sum += s.score * dim.weight;
        weightSum += dim.weight;
      }
    }
    return weightSum > 0 ? (sum / weightSum).toFixed(1) : "—";
  };

  return (
    <div style={{ fontFamily: "system-ui", padding: "24px", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Experiment Evaluation Controller
      </h1>

      <button
        onClick={runEvaluation}
        disabled={running}
        style={{
          padding: "10px 20px",
          fontSize: 14,
          fontWeight: 600,
          background: running ? "#999" : "#2563eb",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          cursor: running ? "not-allowed" : "pointer",
          marginBottom: 24,
        }}
      >
        {running
          ? `Evaluating... (${progress.done}/${progress.total})`
          : "Run Multi-Agent Evaluation"}
      </button>

      {/* Comparison Matrix */}
      {Object.keys(results).length > 0 && (
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>
            Scorecard
          </h2>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: 13,
              marginBottom: 24,
            }}
          >
            <thead>
              <tr style={{ borderBottom: "2px solid #333" }}>
                <th style={{ textAlign: "left", padding: 8 }}>Variant</th>
                {DIMENSIONS.map((d) => (
                  <th key={d.id} style={{ textAlign: "center", padding: 8 }}>
                    {d.label}
                  </th>
                ))}
                <th style={{ textAlign: "center", padding: 8, fontWeight: 700 }}>
                  Weighted Avg
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.values(results).map((r) => (
                <tr key={r.variant.id} style={{ borderBottom: "1px solid #ddd" }}>
                  <td style={{ padding: 8, fontWeight: 600 }}>{r.variant.name}</td>
                  {DIMENSIONS.map((d) => {
                    const s = r.scores[d.id];
                    const score = s?.score || "—";
                    const bg =
                      score >= 8
                        ? "#dcfce7"
                        : score >= 6
                        ? "#fef9c3"
                        : score >= 1
                        ? "#fee2e2"
                        : "transparent";
                    return (
                      <td
                        key={d.id}
                        style={{
                          textAlign: "center",
                          padding: 8,
                          background: bg,
                        }}
                        title={s?.justification || ""}
                      >
                        {score}/10
                      </td>
                    );
                  })}
                  <td
                    style={{
                      textAlign: "center",
                      padding: 8,
                      fontWeight: 700,
                    }}
                  >
                    {computeWeightedAvg(r.scores)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Detailed Results */}
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>
            Detailed Agent Assessments
          </h2>
          {Object.values(results).map((r) => (
            <details
              key={r.variant.id}
              style={{
                marginBottom: 12,
                border: "1px solid #ddd",
                borderRadius: 6,
                padding: 12,
              }}
            >
              <summary style={{ fontWeight: 600, cursor: "pointer" }}>
                {r.variant.name} — Avg:{" "}
                {computeWeightedAvg(r.scores)}
              </summary>
              {DIMENSIONS.map((d) => {
                const s = r.scores[d.id];
                if (!s) return null;
                return (
                  <div
                    key={d.id}
                    style={{
                      marginTop: 12,
                      paddingLeft: 12,
                      borderLeft: "3px solid #2563eb",
                    }}
                  >
                    <strong>
                      {d.label}: {s.score}/10
                    </strong>
                    <p style={{ margin: "4px 0", color: "#555" }}>
                      {s.justification}
                    </p>
                    {s.strengths?.length > 0 && (
                      <p style={{ color: "#16a34a", margin: "2px 0" }}>
                        + {s.strengths.join(", ")}
                      </p>
                    )}
                    {s.weaknesses?.length > 0 && (
                      <p style={{ color: "#dc2626", margin: "2px 0" }}>
                        − {s.weaknesses.join(", ")}
                      </p>
                    )}
                  </div>
                );
              })}
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
