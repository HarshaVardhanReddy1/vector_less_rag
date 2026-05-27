import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

function MetricChip({ label, value }) {
  const score = parseFloat(value);
  const colorClass =
    score >= 0.75 ? "metric-chip--high" : score >= 0.45 ? "metric-chip--medium" : "metric-chip--low";
  return (
    <div className={`metric-chip ${colorClass}`}>
      <span className="metric-chip__label">{label}</span>
      <span className="metric-chip__value">{isNaN(score) ? "—" : score.toFixed(2)}</span>
    </div>
  );
}

function AssistantBubble({ entry }) {
  const [reasoningOpen, setReasoningOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(entry.answer || "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="chat-bubble chat-bubble--assistant">
      <div className="chat-bubble__top-row">
        <span className="chat-label">Assistant</span>
        <button className="copy-btn" onClick={handleCopy} title="Copy answer">
          {copied ? "✓ Copied" : "⎘ Copy"}
        </button>
      </div>

      <div className="markdown-body">
        <ReactMarkdown>{entry.answer}</ReactMarkdown>
      </div>

      {entry.reasoning && (
        <div className="reasoning-panel">
          <button
            className="reasoning-panel__toggle"
            onClick={() => setReasoningOpen((o) => !o)}
          >
            <span className="reasoning-panel__label">Reasoning</span>
            <span className="reasoning-panel__chevron">{reasoningOpen ? "▲" : "▼"}</span>
          </button>
          {reasoningOpen && (
            <p className="reasoning-panel__text">{entry.reasoning}</p>
          )}
        </div>
      )}

      {(entry.confidence || entry.metrics) && (
        <div className="metrics-row">
          {entry.confidence && (
            <span className={`confidence-badge confidence-badge--${entry.confidence}`}>
              {entry.confidence} confidence
            </span>
          )}
          {entry.metrics && (
            <>
              <MetricChip label="Accuracy" value={entry.metrics.accuracy_score} />
              <MetricChip label="Groundedness" value={entry.metrics.groundedness_score} />
              <MetricChip label="Relevance" value={entry.metrics.relevance_score} />
            </>
          )}
        </div>
      )}

      {entry.selectedNode ? (
        <div className="node-summary">
          <div className="node-summary__title">{entry.selectedNode.title}</div>
          <div className="node-summary__meta">
            <span>ID: {entry.selectedNode.node_id}</span>
            <span>Pages: {entry.selectedNode.start_index} – {entry.selectedNode.end_index}</span>
          </div>
        </div>
      ) : (
        <div className="node-summary node-summary--empty">
          <span>No matching node was selected for this query.</span>
        </div>
      )}
    </div>
  );
}

function ChatWindow({ selectedDocument, history, query, setQuery, onSend, isQuerying, onClearChat }) {
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    await onSend(query.trim());
  };

  // Enter to send, Shift+Enter for newline
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (query.trim() && selectedDocument && !isQuerying) {
        onSend(query.trim());
      }
    }
  };

  return (
    <section className="chat-window">
      <div className="chat-header">
        <div>
          <p className="eyebrow">Chat</p>
          <h2>{selectedDocument ? selectedDocument.document_name : "Select a document to start"}</h2>
        </div>
        <div className="chat-header__right">
          <span className="chat-meta">
            {selectedDocument ? `${selectedDocument.total_pages || 0} pages indexed` : "No document selected"}
          </span>
          {history.length > 0 && (
            <button className="button button--ghost button--sm" type="button" onClick={onClearChat}>
              Clear chat
            </button>
          )}
        </div>
      </div>

      <div className="chat-panel">
        {history.length || isQuerying ? (
          <div className="chat-thread">
            {history.map((entry, index) => (
              <div className="chat-pair" key={`entry-${index}`}>
                <div className="chat-bubble chat-bubble--user">
                  <span className="chat-label">You</span>
                  <p>{entry.query}</p>
                </div>
                <AssistantBubble entry={entry} />
              </div>
            ))}

            {isQuerying && (
              <div className="chat-pair">
                <div className="chat-bubble chat-bubble--assistant chat-bubble--typing">
                  <span className="chat-label">Assistant</span>
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        ) : (
          <div className="chat-empty">
            <div className="chat-empty__icon">💬</div>
            <p className="chat-empty__title">No messages yet</p>
            <span className="chat-empty__hint">
              {selectedDocument
                ? "Ask a question about this document below."
                : "Select a document from the sidebar first."}
            </span>
          </div>
        )}
      </div>

      <form className="chat-input-panel" onSubmit={handleSubmit}>
        <div className="chat-input-row">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedDocument
                ? "Ask a question… (Enter to send, Shift+Enter for new line)"
                : "Select a document first."
            }
            disabled={!selectedDocument || isQuerying}
            rows={3}
          />
          <button
            className="button button--primary chat-send-btn"
            type="submit"
            disabled={!selectedDocument || isQuerying || !query.trim()}
          >
            {isQuerying ? "…" : "↑"}
          </button>
        </div>
      </form>
    </section>
  );
}

export default ChatWindow;
