import { ArrowUp, BookOpen, Copy, MessageSquare, Sparkles, X, ChevronUp as ScrollUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function AssistantMessage({ entry }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(entry.answer || "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="assistant-msg">
      <div className={`assistant-msg__avatar${entry.streaming ? " typing-avatar-pulse" : ""}`}>
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
              {!entry.streaming && (
                <button
                  className={`copy-btn${copied ? " copy-btn--copied" : ""}`}
                  onClick={handleCopy}
                >
                  <Copy size={11} />
                  {copied ? "Copied" : "Copy"}
                </button>
              )}
            </div>
          </div>
          <div className="answer-card__body">
            {entry.streaming && !entry.answer ? (
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            ) : (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.answer}</ReactMarkdown>
                {entry.streaming && <span className="stream-cursor" />}
              </div>
            )}
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
                  {node.page && <span className="source-chip__page">p.{node.page}</span>}
                </div>
              ))}
            </div>
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
  const chatAreaRef = useRef(null);
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, isQuerying]);

  const handleScroll = () => {
    const el = chatAreaRef.current;
    if (!el) return;
    setShowScrollTop(el.scrollTop > 300);
  };

  const scrollToTop = () => {
    chatAreaRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  };

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

  const handleTextareaInput = (e) => {
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 130)}px`;
    setQuery(el.value);
  };

  const handleClearInput = () => {
    setQuery("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.focus();
    }
  };

  const showEmpty = !history.length && !isQuerying;

  return (
    <>
      <div className="chat-area" ref={chatAreaRef} onScroll={handleScroll}>
        {showEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty__orb">
              <MessageSquare size={20} />
            </div>
            <p className="chat-empty__text">
              {selectedDocument
                ? `Ask anything about "${selectedDocument.document_name}"`
                : "Select a document from the sidebar to begin."}
            </p>
          </div>
        ) : (
          <div className="chat-thread">
            {history.map((entry, i) => (
              <div className="message-pair" key={i}>
                <div className="user-msg">
                  <div className="user-msg__bubble">{entry.query}</div>
                  {entry.timestamp && (
                    <span className="msg-timestamp">{formatTime(entry.timestamp)}</span>
                  )}
                </div>
                <AssistantMessage entry={entry} />
              </div>
            ))}


            <div ref={bottomRef} />
          </div>
        )}

        <button
          className={`scroll-top-btn${showScrollTop ? " scroll-top-btn--visible" : ""}`}
          onClick={scrollToTop}
          type="button"
          title="Scroll to top"
        >
          <ScrollUp size={14} />
        </button>
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
                    ? "Ask a question…"
                    : "Select a document first."
                }
                disabled={!selectedDocument || isQuerying}
                rows={1}
              />
              {query && (
                <button
                  type="button"
                  className="input-clear-btn"
                  onClick={handleClearInput}
                  tabIndex={-1}
                >
                  <X size={13} />
                </button>
              )}
              <button
                className="send-btn"
                type="submit"
                disabled={!selectedDocument || isQuerying || !query.trim()}
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}

export default ChatWindow;
