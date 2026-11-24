import React, { useState } from 'react';
import { 
  Shield, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Clock, 
  Copy, 
  Check, 
  Terminal,
  Layers,
  FileText,
  Zap,
  Activity
} from 'lucide-react';

const CATEGORIZED_PRESETS = [
  {
    category: "💼 HR & Company Policies",
    questions: [
      { label: "💰 Meal Reimbursement", query: "What is the daily meal reimbursement limit during business travel?" },
      { label: "💻 Tech Stipend", query: "What is the equipment stipend for new hires at AcroCorp?" },
      { label: "🏖️ PTO & Rollover", query: "How many PTO days do full-time employees receive and what is the carryover limit?" },
      { label: "📚 Learning Budget", query: "What is the annual learning and professional development budget per employee?" }
    ]
  },
  {
    category: "☁️ Cloud Infra & Architecture",
    questions: [
      { label: "☸️ Kubernetes HPA", query: "What are the Kubernetes cluster deployment policies and autoscaling HPA guidelines?" },
      { label: "🔒 Vault Secrets", query: "How does HashiCorp Vault manage KV v2 secret engines and DB credential rotation?" },
      { label: "⚡ API Rate Limits", query: "What are the API rate limits and timeouts for the Cloud Engine Pro tier?" },
      { label: "🔄 AWS DR Recovery", query: "What are the RTO and RPO targets for AWS Multi-Region disaster recovery?" }
    ]
  },
  {
    category: "🔧 Troubleshooting & Error Codes",
    questions: [
      { label: "🔑 ERR-401 Token", query: "How do I resolve error ERR-401 authentication token expired?" },
      { label: "🚨 P1 Incident SLA", query: "What is the initial response SLA and coverage for P1 Critical incidents?" },
      { label: "🚫 ERR-429 Rate Limit", query: "How do I fix ERR-429 Rate Exceeded client error?" }
    ]
  },
  {
    category: "🔒 Security & Compliance",
    questions: [
      { label: "📜 SOC 2 Type II", query: "What trust service criteria are audited under AcroCorp's SOC 2 Type II compliance?" },
      { label: "🔐 GDPR Data Rights", query: "What is the timeline for processing GDPR Data Subject Access Requests (DSAR)?" },
      { label: "🏥 HIPAA Encryption", query: "What encryption standards are required for HIPAA Protected Health Information (PHI)?" }
    ]
  },
  {
    category: "🛑 Fallback Safety Tests",
    questions: [
      { label: "👶 Sabbatical Policy", query: "How many days of paid sabbatical do employees receive after 5 years?" },
      { label: "📈 401(k) Match", query: "Does AcroCorp provide a 401(k) retirement matching program?" },
      { label: "🚀 GPU Node Pricing", query: "What is the hourly pricing for NVIDIA H100 GPU clusters on Cloud Engine?" }
    ]
  }
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (qText) => {
    const activeQuery = qText || question;
    if (!activeQuery.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: activeQuery.trim(), max_retries: 2 }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to reach FastAPI backend server.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleCopy = () => {
    if (!result?.final_response) return;
    navigator.clipboard.writeText(result.final_response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getNodeClass = (stepStr) => {
    if (stepStr.includes("Retrieve")) return "node-retrieve";
    if (stepStr.includes("Generate")) return "node-generate";
    if (stepStr.includes("Passed fact-check")) return "node-critique-pass";
    if (stepStr.includes("Failed fact-check")) return "node-critique-fail";
    if (stepStr.includes("Reformulate")) return "node-reformulate";
    if (stepStr.includes("Fallback")) return "node-fallback";
    if (stepStr.includes("Finalize")) return "node-finalize";
    return "";
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-badge">
          <span className="pulse-dot"></span>
          Hybrid Retrieval • Cross-Encoder Reranking • Redis Cache
        </div>
        <h1 className="app-title">Self-Healing RAG</h1>
        <p className="app-subtitle">
          Stateful LangGraph architecture indexing 180+ Enterprise Knowledge Base documents with claim-level citations and latency observability.
        </p>
      </header>

      {/* Categorized Presets */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "center", marginBottom: "0.75rem" }}>
          💡 Explore Demo Questions by Domain (Click to Query)
        </div>
        
        {CATEGORIZED_PRESETS.map((cat, cIdx) => (
          <div key={cIdx} style={{ marginBottom: "0.75rem", textAlign: "center" }}>
            <div style={{ fontSize: "0.78rem", color: "#A5B4FC", fontWeight: 600, marginBottom: "0.3rem" }}>
              {cat.category}
            </div>
            <div className="presets-group" style={{ marginBottom: 0 }}>
              {cat.questions.map((item, qIdx) => (
                <button
                  key={qIdx}
                  className="preset-chip"
                  onClick={() => {
                    setQuestion(item.query);
                    handleSubmit(item.query);
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Input Form */}
      <div className="search-card">
        <textarea
          className="search-input"
          placeholder="Ask any question across HR, Kubernetes, AWS, Vault, SOC2, APIs, or Error Codes..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="search-actions">
          <div className="search-hint">
            <Sparkles size={14} /> Press Ctrl + Enter to run query
          </div>
          <button
            className="submit-btn"
            onClick={() => handleSubmit()}
            disabled={loading || !question.trim()}
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="spin" style={{ animation: "spin 1s linear infinite" }} />
                Evaluating Graph...
              </>
            ) : (
              <>
                <Send size={16} />
                Run Graph
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="results-card" style={{ borderLeft: "4px solid #F43F5E", marginBottom: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#FB7185", fontWeight: 600 }}>
            <AlertTriangle size={18} /> API Connection Error
          </div>
          <p style={{ marginTop: "0.5rem", color: "#9CA3AF", fontSize: "0.95rem" }}>
            {error}. Make sure FastAPI is running (`uvicorn src.api:app --reload --port 8000`).
          </p>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="results-card">
          {/* Metrics Row */}
          <div className="metrics-bar">
            <div>
              {result.grounded && !result.fallback ? (
                <span className="badge-pill badge-grounded">
                  <CheckCircle2 size={15} /> Verified Grounded
                </span>
              ) : (
                <span className="badge-pill badge-fallback">
                  <Shield size={15} /> Safe Fallback Triggered
                </span>
              )}

              {result.trace?.cache_hit && (
                <span className="badge-pill" style={{ background: "rgba(99, 102, 241, 0.15)", color: "#A5B4FC", marginLeft: "0.5rem", border: "1px solid rgba(99, 102, 241, 0.3)" }}>
                  <Zap size={13} /> Cache Hit
                </span>
              )}
            </div>

            <div style={{ display: "flex", gap: "0.5rem" }}>
              <span className="stat-pill">
                <Layers size={13} /> Hybrid Search + Rerank
              </span>
              <span className="stat-pill">
                <RefreshCw size={13} /> {result.retry_count} / 2 Retries
              </span>
              <span className="stat-pill">
                <Clock size={13} /> {result.trace?.latency_ms?.total_ms || 0} ms
              </span>
            </div>
          </div>

          {/* Latency Breakdown Bar */}
          {result.trace?.latency_ms && (
            <div style={{ display: "flex", gap: "1rem", fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "1.25rem", padding: "0.5rem 0.75rem", background: "rgba(0,0,0,0.2)", borderRadius: "8px" }}>
              <span><b>Retrieval:</b> {result.trace.latency_ms.retrieval_ms}ms</span>
              <span><b>Rerank:</b> {result.trace.latency_ms.reranking_ms}ms</span>
              <span><b>Generate:</b> {result.trace.latency_ms.generation_ms}ms</span>
              <span><b>Critique:</b> {result.trace.latency_ms.critique_ms}ms</span>
            </div>
          )}

          {/* Final Answer Card */}
          <div className="answer-box">
            <button className="copy-btn" onClick={handleCopy} title="Copy Answer">
              {copied ? <Check size={14} style={{ color: "#34D399" }} /> : <Copy size={14} />}
              {copied ? "Copied" : "Copy"}
            </button>
            <div style={{ fontWeight: 600, color: "#9CA3AF", fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>
              Final Answer
            </div>
            {result.final_response}
          </div>

          {/* Source Citations */}
          {result.citations && result.citations.length > 0 && (
            <div style={{ marginBottom: "1.75rem" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.6rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <FileText size={15} /> Source Citations Provenance
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {result.citations.map((c) => (
                  <div key={c.citation_id} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "0.4rem 0.75rem", fontSize: "0.82rem" }}>
                    <span style={{ color: "#818CF8", fontWeight: 700 }}>[{c.citation_id}]</span> <span style={{ color: "#E5E7EB" }}>{c.source}</span> <span style={{ color: "#9CA3AF", fontSize: "0.75rem" }}>(Score: {c.relevance_score})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trace Timeline */}
          <div className="timeline-title">
            <Terminal size={16} /> Graph Execution Trajectory
          </div>

          <div className="timeline-list">
            {result.trace_log?.map((step, i) => (
              <div key={i} className={`timeline-node ${getNodeClass(step)}`}>
                {step}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        Stateful LangGraph • Hybrid Search + CrossEncoder • 183 Docs • Redis Cache • FastAPI
      </footer>
    </div>
  );
}
