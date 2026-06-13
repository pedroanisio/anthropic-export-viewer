# Claude React Design System — Artifact Reference

This file contains the design tokens, component patterns, and hard
constraints extracted from `claude-react-design-system.jsx` (v1.0).
When building React `.jsx` artifacts for the multi-agent deliberation
skill, apply these tokens and patterns **instead of** ad-hoc Tailwind
or improvised inline styles.

---

## 1. Hard Constraints (violating these breaks the artifact)

| Rule | Detail |
|---|---|
| No `localStorage` / `sessionStorage` | APIs blocked. Use `useState`, `useReducer`, or `window.storage` (async, 5 MB/key). |
| No `<form>` tags in React | Use `onClick` / `onChange` handlers on buttons and inputs directly. |
| Single default export, no required props | Artifact must render standalone with zero config. |
| Tailwind **core** classes only | No JIT compiler, no arbitrary values like `w-[347px]`. Use inline styles for precision. |
| Scripts execute after streaming | Interactive elements appear inert until full render completes. |
| Three.js is r128 | No `THREE.CapsuleGeometry`. (Not relevant for this skill, but listed for completeness.) |
| External scripts: `cdnjs.cloudflare.com` only | The only allowed CDN for external scripts. |

---

## 2. Font Loader

Import this single URL in a `useEffect` or inline `<link>`:

```
https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap
```

---

## 3. Design Tokens

### 3.1 Color Primitives

Define these as CSS custom properties via an inline `<style>` tag.
Toggle between light and dark by setting `data-theme` on `document.documentElement`.

```js
const COLORS = {
  ink:           { light: "#1a1a2e", dark: "#e8e6e1" },
  paper:         { light: "#f7f5f0", dark: "#141418" },
  muted:         { light: "#6b6b7b", dark: "#8a8a96" },
  border:        { light: "#d4d2cc", dark: "#2a2a32" },
  surface:       { light: "#ffffff", dark: "#1c1c22" },
  surfaceRaised: { light: "#ffffff", dark: "#222228" },
  accent:        { light: "#c45d3e", dark: "#e07a5a" },
  accentMuted:   { light: "rgba(196,93,62,0.08)", dark: "rgba(224,122,90,0.1)" },
  success:       { light: "#3a7d5c", dark: "#5cb882" },
  warning:       { light: "#b8860b", dark: "#daa520" },
  danger:        { light: "#c0392b", dark: "#e74c3c" },
  info:          { light: "#2c6fbb", dark: "#5a9fd4" },
};
```

Inject them:

```jsx
<style>{`
  :root {
    --ink: ${COLORS.ink.light}; --paper: ${COLORS.paper.light};
    --muted: ${COLORS.muted.light}; --border: ${COLORS.border.light};
    --surface: ${COLORS.surface.light}; --surface-raised: ${COLORS.surfaceRaised.light};
    --accent: ${COLORS.accent.light}; --accent-muted: ${COLORS.accentMuted.light};
    --success: ${COLORS.success.light}; --warning: ${COLORS.warning.light};
    --danger: ${COLORS.danger.light}; --info: ${COLORS.info.light};
  }
  [data-theme="dark"] {
    --ink: ${COLORS.ink.dark}; --paper: ${COLORS.paper.dark};
    --muted: ${COLORS.muted.dark}; --border: ${COLORS.border.dark};
    --surface: ${COLORS.surface.dark}; --surface-raised: ${COLORS.surfaceRaised.dark};
    --accent: ${COLORS.accent.dark}; --accent-muted: ${COLORS.accentMuted.dark};
    --success: ${COLORS.success.dark}; --warning: ${COLORS.warning.dark};
    --danger: ${COLORS.danger.dark}; --info: ${COLORS.info.dark};
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; }
  ::selection { background: var(--accent); color: #fff; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
`}</style>
```

### 3.2 Agent Role Colors

Map the four deliberation agents to semantic colors already in the palette:

| Agent | CSS Variable | Rationale |
|---|---|---|
| Decomposer | `var(--info)` | Analytical blue — structural decomposition |
| Strategist | `var(--success)` | Constructive green — solution-building |
| Critic | `var(--danger)` | Alert red — adversarial challenge |
| Synthesizer | `var(--accent)` | Warm terracotta — synthesis and convergence |

For light tinted backgrounds per agent, use `rgba()` at 0.08–0.10 opacity
of the agent's color (same pattern as `--accent-muted`).

### 3.3 Typography Stacks

```js
const FONTS = {
  display: "'Playfair Display', Georgia, 'Times New Roman', serif",    // Heroes, large headings
  heading: "'DM Sans', 'Helvetica Neue', Helvetica, sans-serif",       // Section headings, labels
  body:    "'Source Sans 3', 'Segoe UI', sans-serif",                   // Paragraphs, UI text
  mono:    "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",     // Code, data, tokens
};
```

Usage guidance:
- **Display** font for the main artifact title (e.g. "Multi-Agent Deliberation").
- **Heading** font for agent names, round headers, section labels.
- **Body** font for agent output prose, descriptions, helper text.
- **Mono** font for JSON convergence verdicts, token counts, structured data.

### 3.4 Type Scale (reference)

| Name | Size | Line Height | Tracking |
|---|---|---|---|
| xs | 0.75rem | 1rem | 0.01em |
| sm | 0.875rem | 1.25rem | 0 |
| base | 1rem | 1.5rem | 0 |
| lg | 1.125rem | 1.75rem | −0.01em |
| xl | 1.25rem | 1.75rem | −0.015em |
| 2xl | 1.5rem | 2rem | −0.02em |
| 3xl | 1.875rem | 2.25rem | −0.025em |
| 4xl | 2.25rem | 2.5rem | −0.03em |

### 3.5 Spacing

Use these values for `padding`, `gap`, `margin`:

| Token | Value |
|---|---|
| 4xs | 2px |
| 3xs | 4px |
| 2xs | 6px |
| xs | 8px |
| sm | 12px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| 2xl | 48px |
| 3xl | 64px |

### 3.6 Border Radii

| Token | Value | Use |
|---|---|---|
| sm | 4px | Badges, small chips |
| md | 8px | Buttons, inputs |
| lg | 12px | Cards, panels |
| xl | 16px | Large cards, modals |
| full | 9999px | Pills, circular badges |

### 3.7 Shadows

Light mode:
- **sm**: `0 1px 2px rgba(0,0,0,0.04)`
- **md**: `0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)`
- **lg**: `0 8px 24px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)`

Dark mode:
- **sm**: `0 1px 2px rgba(0,0,0,0.3)`
- **md**: `0 2px 8px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.2)`
- **lg**: `0 8px 24px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3)`

### 3.8 Motion

| Duration | Value | Use |
|---|---|---|
| instant | 100ms | Micro-feedback (checks, toggles) |
| fast | 150ms | Hover states, small reveals |
| normal | 250ms | Panels, modals, transitions |
| slow | 400ms | Page transitions, orchestrated reveals |

Easings:
- **ease-out**: `cubic-bezier(0.22, 1, 0.36, 1)` — elements entering (default)
- **ease-in**: `cubic-bezier(0.55, 0, 1, 0.45)` — elements exiting
- **spring**: `cubic-bezier(0.34, 1.56, 0.64, 1)` — playful overshoot

Stagger pattern for agent cards mounting:

```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.stagger > * {
  opacity: 0;
  animation: fadeUp 400ms cubic-bezier(0.22,1,0.36,1) forwards;
}
.stagger > *:nth-child(1) { animation-delay: 0ms; }
.stagger > *:nth-child(2) { animation-delay: 60ms; }
.stagger > *:nth-child(3) { animation-delay: 120ms; }
.stagger > *:nth-child(4) { animation-delay: 180ms; }
```

---

## 4. Component Patterns

### 4.1 Buttons

```jsx
function Button({ children, variant = "primary", onClick, disabled, style: sx }) {
  const variants = {
    primary:   { bg: "var(--accent)", color: "#fff", border: "none" },
    secondary: { bg: "var(--surface)", color: "var(--ink)", border: "1px solid var(--border)" },
    ghost:     { bg: "transparent", color: "var(--accent)", border: "1px solid transparent" },
    danger:    { bg: "var(--danger)", color: "#fff", border: "none" },
  };
  const v = variants[variant];
  return (
    <button onClick={onClick} disabled={disabled} style={{
      padding: "8px 20px", borderRadius: 8, background: v.bg, color: v.color,
      border: v.border, cursor: disabled ? "not-allowed" : "pointer",
      fontFamily: FONTS.heading, fontSize: "0.85rem", fontWeight: 600,
      transition: "all 150ms ease", opacity: disabled ? 0.5 : 1, ...sx,
    }}
      onMouseEnter={e => { if (!disabled) { e.currentTarget.style.opacity = "0.85"; e.currentTarget.style.transform = "translateY(-1px)"; }}}
      onMouseLeave={e => { e.currentTarget.style.opacity = disabled ? "0.5" : "1"; e.currentTarget.style.transform = ""; }}
    >{children}</button>
  );
}
```

### 4.2 Cards / Panels

```jsx
function Card({ children, elevated, style: sx }) {
  return (
    <div style={{
      padding: 20, borderRadius: 12,
      background: elevated ? "var(--surface-raised)" : "var(--surface)",
      border: "1px solid var(--border)",
      boxShadow: elevated ? "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)" : "none",
      ...sx,
    }}>{children}</div>
  );
}
```

### 4.3 Badges / Pills

```jsx
function Badge({ label, color = "var(--accent)", bg }) {
  return (
    <span style={{
      padding: "3px 10px", borderRadius: 9999, fontSize: "0.72rem", fontWeight: 600,
      fontFamily: FONTS.heading, color,
      background: bg || `color-mix(in srgb, ${color} 10%, transparent)`,
    }}>{label}</span>
  );
}
```

### 4.4 Agent Output Panel (deliberation-specific)

```jsx
function AgentPanel({ agentName, roleColor, content, round, isLoading }) {
  return (
    <div style={{
      padding: 20, borderRadius: 12,
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderLeft: `3px solid ${roleColor}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <Badge label={agentName} color={roleColor} />
        <span style={{ fontFamily: FONTS.mono, fontSize: "0.72rem", color: "var(--muted)" }}>
          Round {round}
        </span>
      </div>
      {isLoading ? (
        <div style={{ fontFamily: FONTS.body, fontSize: "0.85rem", color: "var(--muted)", fontStyle: "italic" }}>
          Thinking...
        </div>
      ) : (
        <div style={{
          fontFamily: FONTS.body, fontSize: "0.88rem", lineHeight: 1.6,
          color: "var(--ink)", whiteSpace: "pre-wrap",
        }}>
          {content}
        </div>
      )}
    </div>
  );
}
```

### 4.5 Section Headings

```jsx
function SectionHeading({ title }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h2 style={{
        fontFamily: FONTS.display, fontSize: "1.5rem", fontWeight: 700,
        color: "var(--ink)", letterSpacing: "-0.02em", marginBottom: 6,
      }}>{title}</h2>
      <div style={{ width: 40, height: 3, background: "var(--accent)", borderRadius: 2 }} />
    </div>
  );
}
```

### 4.6 Textarea (for problem statement input)

```jsx
<textarea
  value={problemStatement}
  onChange={e => setProblemStatement(e.target.value)}
  placeholder="Describe the problem to deliberate on..."
  style={{
    width: "100%", minHeight: 120, padding: "12px 16px",
    borderRadius: 8, border: "1px solid var(--border)",
    background: "var(--surface)", color: "var(--ink)",
    fontFamily: FONTS.body, fontSize: "0.9rem", lineHeight: 1.5,
    outline: "none", resize: "vertical",
    transition: "border-color 150ms ease",
  }}
  onFocus={e => e.target.style.borderColor = "var(--accent)"}
  onBlur={e => e.target.style.borderColor = "var(--border)"}
/>
```

---

## 5. Theme Switching

Include a theme toggle button. Pattern:

```jsx
const [theme, setTheme] = useState("light");

useEffect(() => {
  document.documentElement.setAttribute("data-theme", theme);
}, [theme]);
```

Toggle button using `Sun` / `Moon` icons from `lucide-react`.

---

## 6. File Structure for Deliberation Artifact

The artifact is a **single `.jsx` file** (hard constraint). Organize
with comment-delimited sections:

```jsx
// ─── DESIGN TOKENS ──────────────────────
const COLORS = { ... };
const FONTS  = { ... };

// ─── UTILITY COMPONENTS ─────────────────
function Button(...) { ... }
function Card(...) { ... }
function Badge(...) { ... }
function AgentPanel(...) { ... }

// ─── DELIBERATION ENGINE ────────────────
async function callAgent(systemPrompt, messages) { ... }
async function runRound(roundNum, priorRecord) { ... }

// ─── MAIN APP ───────────────────────────
export default function MultiAgentDeliberation() { ... }
```

### API Call Pattern (correct model and tokens)

The `callAgent` function must use the model strings and `max_tokens`
from `references/agent-prompts.md`. Here is the reference pattern:

```jsx
// Token limits per tier — see references/agent-prompts.md §4
const TIERS = {
  standard: { model: "claude-sonnet-4-6", maxTokens: 8192 },
  complex:  { model: "claude-sonnet-4-6", maxTokens: 16000 },
  heavy:    { model: "claude-opus-4-6",   maxTokens: 32000 },
};

async function callAgent(agentId, systemPrompt, userMessage, temperature = 0.7, tier = "complex") {
  const { model, maxTokens } = TIERS[tier];
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,              // CURRENT model — never use deprecated strings
      max_tokens: maxTokens, // MINIMUM 8192 — lower values truncate JSON
      temperature,
      system: systemPrompt,
      messages: [{ role: "user", content: userMessage }],
    }),
  });
  const data = await response.json();
  if (data.error) throw new Error(data.error.message || "API error");
  const text = data.content?.map(b => b.type === "text" ? b.text : "").join("\n") || "";
  const truncated = data.stop_reason === "max_tokens";
  const tokensUsed = data.usage?.output_tokens || 0;
  return { text, truncated, tokensUsed };
}
```

**Truncation handling is mandatory.** If `stop_reason === "max_tokens"`,
the artifact must surface this visually — a yellow `⚠ TRUNCATED` badge
on the agent panel, plus the token count. Never silently swallow a
truncated response.
