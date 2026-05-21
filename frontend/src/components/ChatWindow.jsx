function ChatWindow({ selectedDocument, history, query, setQuery, onSend, isQuerying }) {
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    await onSend(query.trim());
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
                  <p>{entry.answer}</p>
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
          placeholder={selectedDocument ? "Ask a question about the selected document..." : "Select a document first."}
          disabled={!selectedDocument || isQuerying}
          rows={4}
        />
        <button className="button button--primary" type="submit" disabled={!selectedDocument || isQuerying || !query.trim()}>
          {isQuerying ? "Thinking..." : "Send question"}
        </button>
      </form>
    </section>
  );
}

export default ChatWindow;
