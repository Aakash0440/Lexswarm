// dashboard/src/App.jsx
// LEXSWARM Web Interface — Submit a case, get legal analysis
// Connect to FastAPI at http://localhost:8000

import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const URGENCY_COLORS = {
  CRITICAL: { bg: "#f8d7da", text: "#721c24", label: "Critical — act now" },
  HIGH:     { bg: "#fff3cd", text: "#856404", label: "High — act within 24h" },
  MEDIUM:   { bg: "#d1ecf1", text: "#0c5460", label: "Medium — act within 3 days" },
  LOW:      { bg: "#d4edda", text: "#155724", label: "Low — within a week" },
};

const EXAMPLE_CASES = [
  "My landlord changed the locks tonight in Karachi and I have nowhere to sleep.",
  "My employer has not paid my salary for 3 months in Jakarta and is threatening to fire me.",
  "Police arrested me without a warrant. I don't know what I am charged with.",
  "I received a deportation order but I fear returning to my home country.",
];

function UrgencyBadge({ urgency }) {
  const colors = URGENCY_COLORS[urgency] || URGENCY_COLORS.MEDIUM;
  return (
    <span style={{
      background: colors.bg, color: colors.text,
      padding: "3px 10px", borderRadius: "4px",
      fontSize: "12px", fontWeight: 500,
    }}>
      {colors.label}
    </span>
  );
}

function RightCard({ right }) {
  return (
    <div style={{
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-md)",
      padding: "12px 14px", marginBottom: "8px",
      background: "var(--color-background-primary)",
    }}>
      <div style={{ fontWeight: 500, fontSize: "14px", marginBottom: "4px" }}>
        {right.right}
      </div>
      <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "4px" }}>
        Law: {right.statute}
      </div>
      <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
        {right.plain_english}
      </div>
    </div>
  );
}

function ActionCard({ action }) {
  return (
    <div style={{
      display: "flex", gap: "12px", padding: "10px 0",
      borderBottom: "0.5px solid var(--color-border-tertiary)",
    }}>
      <div style={{
        width: "24px", height: "24px", borderRadius: "50%",
        background: action.requires_human ? "var(--color-background-danger)" : "var(--color-background-info)",
        color: action.requires_human ? "var(--color-text-danger)" : "var(--color-text-info)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "12px", fontWeight: 500, flexShrink: 0,
      }}>
        {action.step_number}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 500, fontSize: "13px" }}>{action.action}</div>
        <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginTop: "2px" }}>
          When: {action.deadline}
        </div>
        <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginTop: "2px" }}>
          {action.how_to}
        </div>
        {action.requires_human && (
          <div style={{
            marginTop: "4px", fontSize: "11px",
            color: "var(--color-text-danger)", fontWeight: 500,
          }}>
            Requires human lawyer
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [description, setDescription] = useState("");
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState(null);
  const [error, setError]             = useState(null);
  const [activeDoc, setActiveDoc]     = useState(null);

  const analyze = async () => {
    if (!description.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const resp = await fetch(`${API_BASE}/cases/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      if (!resp.ok) throw new Error(`API error: ${resp.status}`);
      const data = await resp.json();
      setResult(data);
    } catch (err) {
      setError(`${err.message}. Make sure LEXSWARM API is running: python scripts/run_api.py`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "1rem 0", fontFamily: "var(--font-sans)", maxWidth: "800px" }}>

      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "22px", fontWeight: 500, marginBottom: "6px" }}>
          LEXSWARM Legal Defense
        </div>
        <div style={{ fontSize: "14px", color: "var(--color-text-secondary)" }}>
          Describe your legal situation in any language. Get your rights, a strategy, and legal documents instantly.
        </div>
      </div>

      <textarea
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="Describe your situation... (e.g. My landlord locked me out tonight in Karachi)"
        rows={4}
        style={{ width: "100%", fontSize: "14px", padding: "10px", marginBottom: "8px", resize: "vertical" }}
      />

      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", flexWrap: "wrap" }}>
        {EXAMPLE_CASES.map((ex, i) => (
          <button key={i} onClick={() => setDescription(ex)}
            style={{ fontSize: "11px", padding: "3px 8px" }}>
            Example {i + 1}
          </button>
        ))}
      </div>

      <button onClick={analyze} disabled={loading || !description.trim()}
        style={{ marginBottom: "1.5rem", fontSize: "14px", padding: "8px 20px" }}>
        {loading ? "Analyzing..." : "Analyze my case ↗"}
      </button>

      {error && (
        <div style={{
          padding: "12px", background: "var(--color-background-danger)",
          color: "var(--color-text-danger)", borderRadius: "var(--border-radius-md)",
          fontSize: "13px", marginBottom: "1rem",
        }}>
          {error}
        </div>
      )}

      {result && (
        <div>
          <div style={{
            background: "var(--color-background-secondary)",
            borderRadius: "var(--border-radius-lg)",
            padding: "16px", marginBottom: "1.25rem",
            display: "grid", gridTemplateColumns: "repeat(4, minmax(0,1fr))", gap: "10px",
          }}>
            {[
              { label: "Case ID",   value: result.case_id },
              { label: "Type",      value: result.case_type },
              { label: "Country",   value: result.country },
              { label: "Language",  value: result.language },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: "11px", color: "var(--color-text-secondary)" }}>{label}</div>
                <div style={{ fontWeight: 500, marginTop: "2px" }}>{value}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap" }}>
            <UrgencyBadge urgency={result.urgency} />
            {result.human_volunteer_alerted && (
              <span style={{ fontSize: "12px", color: "var(--color-text-success)", fontWeight: 500 }}>
                Volunteer lawyer alerted
              </span>
            )}
            {result.simulation && (
              <span style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
                Win probability: {(result.simulation.win_probability * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {result.legal_rights?.length > 0 && (
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "15px", fontWeight: 500, marginBottom: "10px" }}>Your legal rights</div>
              {result.legal_rights.map((r, i) => <RightCard key={i} right={r} />)}
            </div>
          )}

          {result.recommended_actions?.length > 0 && (
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "15px", fontWeight: 500, marginBottom: "10px" }}>Action plan</div>
              {result.recommended_actions.map((a, i) => <ActionCard key={i} action={a} />)}
            </div>
          )}

          {result.simulation && (
            <div style={{
              background: "var(--color-background-secondary)",
              borderRadius: "var(--border-radius-md)", padding: "14px", marginBottom: "1.25rem",
            }}>
              <div style={{ fontSize: "15px", fontWeight: 500, marginBottom: "8px" }}>Courtroom strategy</div>
              <div style={{ fontSize: "13px", marginBottom: "6px" }}>{result.simulation.recommended_strategy}</div>
              {result.simulation.judge_concerns?.length > 0 && (
                <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
                  Judge will likely ask: {result.simulation.judge_concerns[0]}
                </div>
              )}
            </div>
          )}

          {result.documents?.length > 0 && (
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "15px", fontWeight: 500, marginBottom: "10px" }}>Generated documents</div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                {result.documents.map((doc, i) => (
                  <button key={i} onClick={() => setActiveDoc(activeDoc === i ? null : i)}
                    style={{ fontSize: "12px", padding: "5px 12px",
                      background: activeDoc === i ? "var(--color-background-info)" : undefined,
                      color: activeDoc === i ? "var(--color-text-info)" : undefined }}>
                    {doc.title}
                  </button>
                ))}
              </div>
              {activeDoc !== null && result.documents[activeDoc] && (
                <div style={{
                  background: "var(--color-background-secondary)",
                  borderRadius: "var(--border-radius-md)", padding: "14px",
                  fontFamily: "var(--font-mono)", fontSize: "12px",
                  whiteSpace: "pre-wrap", maxHeight: "400px", overflowY: "auto",
                }}>
                  {result.documents[activeDoc].content}
                </div>
              )}
            </div>
          )}

          <div style={{ fontSize: "11px", color: "var(--color-text-secondary)", marginTop: "1rem" }}>
            Not legal advice. Review all documents with a qualified lawyer before filing.
          </div>
        </div>
      )}
    </div>
  );
}
