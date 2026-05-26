import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

function ChatWindow({ selectedDocument, history, query, setQuery, onSend, isQuerying }) {
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
        <span className="chat-meta">
          {selectedDocument ? `${selectedDocument.total_pages || 0} pages indexed` : "No document selected"}
        </span>
      </div>

      <div className="chat-panel">
        {history.length ? (
          <div className="chat-thread">
            {history.map((entry, index) => (
              <div className="chat-pair" key={`entry-${index}`}>
                <div className="chat-bubble chat-bubble--user">
                  <span className="chat-label">You</span>
                  <p>{entry.query}</p>
                </div>
                <div className="chat-bubble chat-bubble--assistant">
                  <span className="chat-label">Assistant</span>
                  <div className="markdown-body">
                    <ReactMarkdown>{entry.answer}</ReactMarkdown>
                  </div>

                  {entry.reasoning && (
                    <div className="reasoning-panel">
                      <span className="reasoning-panel__label">Reasoning</span>
                      <p className="reasoning-panel__text">{entry.reasoning}</p>
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
                          <div className="metric-chip">
                            <span className="metric-chip__label">Accuracy</span>
                            <span className="metric-chip__value">{entry.metrics.accuracy_score ?? "—"}</span>
                          </div>
                          <div className="metric-chip">
                            <span className="metric-chip__label">Groundedness</span>
                            <span className="metric-chip__value">{entry.metrics.groundedness_score ?? "—"}</span>
                          </div>
                          <div className="metric-chip">
                            <span className="metric-chip__label">Relevance</span>
                            <span className="metric-chip__value">{entry.metrics.relevance_score ?? "—"}</span>
                          </div>
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
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        ) : (
          <div className="chat-empty">
            <p>Ask a question to see answers from the indexed document.</p>
          </div>
        )}
      </div>

      <form className="chat-input-panel" onSubmit={handleSubmit}>
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
          rows={4}
        />
        <button
          className="button button--primary"
          type="submit"
          disabled={!selectedDocument || isQuerying || !query.trim()}
        >
          {isQuerying ? "Thinking..." : "Send question"}
        </button>
      </form>
    </section>
  );
}

export default ChatWindow;
