import { BarChart2, BookOpen, Brain, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

function ScoreCard({ label, value }) {
  const score = parseFloat(value);
  const pct = isNaN(score) ? 0 : Math.round(score * 100);
  const tier = score >= 0.75 ? "high" : score >= 0.45 ? "med" : "low";

  return (
    <div className="score-card">
      <div className="score-card__row">
        <span className="score-card__name">{label}</span>
        <span className={`score-card__val score-card__val--${tier}`}>
          {isNaN(score) ? "—" : score.toFixed(2)}
        </span>
      </div>
      <div className="score-bar">
        <div
          className={`score-bar__fill score-bar__fill--${tier}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function InsightsPanel({ open, entry }) {
  const [reasoningOpen, setReasoningOpen] = useState(false);

  return (
    <aside className={`insights-panel${open ? "" : " insights-panel--collapsed"}`}>
      <div className="insights-panel__inner">
        <div className="insights-panel__head">
          <span className="insights-panel__title">
            <BarChart2 size={12} />
            Analysis
          </span>
        </div>

        {entry ? (
          <div className="insights-scroll">
            {entry.confidence && (
              <div className="insights-block">
                <span className="insights-block__label">Confidence</span>
                <div
                  className={`confidence-pill confidence-pill--${entry.confidence}`}
                  style={{ alignSelf: "flex-start", padding: "5px 12px", fontSize: "12px" }}
                >
                  {entry.confidence.charAt(0).toUpperCase() + entry.confidence.slice(1)} confidence
                </div>
              </div>
            )}

            {entry.metrics && (
              <div className="insights-block">
                <span className="insights-block__label">Evaluation scores</span>
                <ScoreCard label="Accuracy" value={entry.metrics.accuracy_score} />
                <ScoreCard label="Groundedness" value={entry.metrics.groundedness_score} />
                <ScoreCard label="Relevance" value={entry.metrics.relevance_score} />
              </div>
            )}

            {entry.selectedNodes?.length > 0 && (
              <div className="insights-block">
                <span className="insights-block__label">
                  <BookOpen size={10} style={{ display: "inline", marginRight: 3 }} />
                  Retrieved sections ({entry.selectedNodes.length})
                </span>
                {entry.selectedNodes.map((node) => (
                  <div className="source-node" key={node.node_id}>
                    <span className="source-node__id">{node.node_id}</span>
                    <span className="source-node__title">{node.title}</span>
                  </div>
                ))}
              </div>
            )}

            {entry.reasoning && (
              <div className="insights-block">
                <span className="insights-block__label">
                  <Brain size={10} style={{ display: "inline", marginRight: 3 }} />
                  Reasoning
                </span>
                <button
                  className="reasoning-toggle"
                  style={{ borderRadius: "var(--r-md) var(--r-md) 0 0" }}
                  onClick={() => setReasoningOpen((o) => !o)}
                >
                  <span className="reasoning-toggle__left">
                    <span style={{ fontSize: 11, color: "var(--text-3)" }}>
                      {reasoningOpen ? "Hide trace" : "Show trace"}
                    </span>
                  </span>
                  {reasoningOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>
                {reasoningOpen && (
                  <div
                    className="reasoning-box"
                    style={{ borderRadius: "0 0 var(--r-md) var(--r-md)", borderTop: "none" }}
                  >
                    {entry.reasoning}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="insights-empty">
            <div className="insights-empty__icon">
              <BarChart2 size={18} />
            </div>
            <span className="insights-empty__text">
              Ask a question to see retrieval analysis and evaluation scores.
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}

export default InsightsPanel;
