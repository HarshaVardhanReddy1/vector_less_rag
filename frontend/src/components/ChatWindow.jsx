import { ArrowUp, BookOpen, Brain, ChevronDown, ChevronUp, Copy, FileText, Layers, MessageSquare, Sparkles, Zap } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SUGGESTIONS = [
  { icon: <FileText size={12} />, text: "What is this document about?" },
  { icon: <Layers size={12} />, text: "Summarize the key sections." },
  { icon: <Zap size={12} />, text: "What are the main risks?" },
  { icon: <Brain size={12} />, text: "List all phases and timelines." },
];

function MetricChipSm({ label, value }) {
  const score = parseFloat(value);
  const tier = score >= 0.75 ? "high" : score >= 0.45 ? "med" : "low";
  return (
    <div className={`metric-chip-sm metric-chip-sm--${tier}`}>
      <span className="metric-chip-sm__label">{label}</span>
      <span className="metric-chip-sm__val">{isNaN(score) ? "—" : score.toFixed(2)}</span>
    </div>
  );
}

function AssistantMessage({ entry }) {
  const [reasoningOpen, setReasoningOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(entry.answer || "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="assistant-msg">
      <div className="assistant-msg__avatar">
        <Sparkles size={12} color="#fff" />
      </div>

      <div className="assistant-msg__body">
        <div className="answer-card">
          <div className="answer-card__topbar">
            <span className="answer-card__tag">
              <Sparkles size={9} />
              Answer
            </span>
            <div className="answer-card__acts">
              <button
                className={`copy-btn${copied ? " copy-btn--copied" : ""}`}
                onClick={handleCopy}
              >
                <Copy size={11} />
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
          <div className="answer-card__body">
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.answer}</ReactMarkdown>
            </div>
          </div>
        </div>

        {entry.selectedNodes?.length > 0 && (
          <div className="sources-strip">
            <span className="sources-strip__label">
              <BookOpen size={9} />
              Retrieved sections
            </span>
            <div className="source-chips">
              {entry.selectedNodes.map((node) => (
                <div className="source-chip" key={node.node_id}>
                  <span className="source-chip__id">{node.node_id}</span>
                  <span>{node.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {(entry.confidence || entry.metrics) && (
          <div className="metrics-row">
            {entry.confidence && (
              <div className={`confidence-pill confidence-pill--${entry.confidence}`}>
                {entry.confidence.charAt(0).toUpperCase() + entry.confidence.slice(1)}
              </div>
            )}
            {entry.metrics && (
              <>
                <MetricChipSm label="Accuracy" value={entry.metrics.accuracy_score} />
                <MetricChipSm label="Groundedness" value={entry.metrics.groundedness_score} />
                <MetricChipSm label="Relevance" value={entry.metrics.relevance_score} />
              </>
            )}
          </div>
        )}

        {entry.reasoning && (
          <div className="reasoning-panel">
            <button
              className="reasoning-toggle"
              onClick={() => setReasoningOpen((o) => !o)}
            >
              <span className="reasoning-toggle__left">
                <Brain size={13} className="reasoning-toggle__icon" />
                Reasoning trace
              </span>
              {reasoningOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
            {reasoningOpen && (
              <div className="reasoning-body">{entry.reasoning}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ChatWindow({
  selectedDocument,
  history,
  query,
  setQuery,
  onSend,
  isQuerying,
}) {
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, isQuerying]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || !selectedDocument || isQuerying) return;
    await onSend(query.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (query.trim() && selectedDocument && !isQuerying) {
        onSend(query.trim());
      }
    }
  };

  const handleSuggestion = (text) => {
    setQuery(text);
    textareaRef.current?.focus();
  };

  const handleTextareaInput = (e) => {
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 130)}px`;
    setQuery(el.value);
  };

  const showWelcome = !history.length && !isQuerying;

  return (
    <>
      <div className="chat-area">
        {showWelcome ? (
          <div className="chat-welcome">
            <div className="chat-welcome__orb">
              <MessageSquare size={22} />
            </div>
            <h2 className="chat-welcome__title">
              {selectedDocument ? `Ask about ${selectedDocument.document_name}` : "Select a document"}
            </h2>
            <p className="chat-welcome__sub">
              {selectedDocument
                ? "Ask anything about the indexed content. Answers are grounded in the source document."
                : "Choose a document from the sidebar to start a conversation."}
            </p>
            {selectedDocument && (
              <div className="suggestion-grid">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.text}
                    className="suggestion-chip"
                    onClick={() => handleSuggestion(s.text)}
                    type="button"
                  >
                    <span className="suggestion-chip__icon">{s.icon}</span>
                    {s.text}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="chat-thread">
            {history.map((entry, i) => (
              <div className="message-pair" key={i}>
                <div className="user-msg">
                  <div className="user-msg__bubble">{entry.query}</div>
                </div>
                <AssistantMessage entry={entry} />
              </div>
            ))}

            {isQuerying && (
              <div className="typing-bubble">
                <div className="assistant-msg__avatar">
                  <Sparkles size={12} color="#fff" />
                </div>
                <div className="typing-dots">
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="chat-input-zone">
        <div className="input-wrapper">
          <form onSubmit={handleSubmit}>
            <div className="input-box">
              <textarea
                ref={textareaRef}
                value={query}
                onInput={handleTextareaInput}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedDocument
                    ? "Ask a question… (Enter to send, Shift+Enter for newline)"
                    : "Select a document first."
                }
                disabled={!selectedDocument || isQuerying}
                rows={1}
              />
              <button
                className="send-btn"
                type="submit"
                disabled={!selectedDocument || isQuerying || !query.trim()}
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </form>
          <p className="input-hint">
            {selectedDocument
              ? `${selectedDocument.total_nodes || 0} sections indexed · context-grounded answers`
              : "No document selected"}
          </p>
        </div>
      </div>
    </>
  );
}

export default ChatWindow;
