import { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InsightsPanel from "./components/InsightsPanel";
import Sidebar from "./components/Sidebar";
import StatusBanner from "./components/StatusBanner";
import TopNav from "./components/TopNav";
import {
  fetchDocumentById,
  listDocuments,
  queryDocument,
  uploadDocument,
} from "./api/documentApi";
import "./styles.css";

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [query, setQuery] = useState("");
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [insightsPanelOpen, setInsightsPanelOpen] = useState(true);
  const [activeInsightsEntry, setActiveInsightsEntry] = useState(null);
  const [lastQueriedDocId, setLastQueriedDocId] = useState(null);

  const clearMessages = () => {
    setErrorMessage("");
    setSuccessMessage("");
  };

  const loadDocuments = async (preferredDocumentId) => {
    setIsLoadingDocuments(true);
    clearMessages();
    try {
      const data = await listDocuments();
      const nextDocs = data.documents || [];
      setDocuments(nextDocs);
      const nextId =
        preferredDocumentId ||
        (nextDocs.some((d) => d._id === selectedDocumentId) ? selectedDocumentId : nextDocs[0]?._id || "");
      setSelectedDocumentId(nextId);
      return nextId;
    } catch (err) {
      setErrorMessage(err.message);
      return "";
    } finally {
      setIsLoadingDocuments(false);
      setIsBootstrapping(false);
    }
  };

  useEffect(() => { void loadDocuments(); }, []);

  useEffect(() => {
    if (!selectedDocumentId) { setSelectedDocument(null); return; }
    let active = true;
    (async () => {
      try {
        const doc = await fetchDocumentById(selectedDocumentId);
        if (active) { setSelectedDocument(doc); clearMessages(); }
      } catch (err) {
        if (active) { setSelectedDocument(null); setErrorMessage(err.message); }
      }
    })();
    return () => { active = false; };
  }, [selectedDocumentId]);

  const handleUpload = async (file) => {
    setIsUploading(true);
    clearMessages();
    try {
      const response = await uploadDocument(file);
      await loadDocuments(response.document_id);
      setSuccessMessage(`"${response.document_name}" indexed successfully.`);
      setChatHistory([]);
      setActiveInsightsEntry(null);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectDocument = (id) => {
    setSelectedDocumentId(id);
    setChatHistory([]);
    setActiveInsightsEntry(null);
    clearMessages();
  };

  const handleSend = async (message) => {
    if (!selectedDocument?.tree_json_path || !selectedDocument?.nodes_json_path) {
      setErrorMessage("Please select a valid indexed document before asking a question.");
      return;
    }
    setIsQuerying(true);
    clearMessages();
    try {
      const response = await queryDocument({
        query: message,
        treePath: selectedDocument.tree_json_path,
        nodesPath: selectedDocument.nodes_json_path,
      });
      const entry = {
        query: message,
        answer: response.answer,
        selectedNodes: response.selected_nodes || [],
        reasoning: response.reasoning || "",
        confidence: response.confidence || "",
        metrics: response.metrics || {},
        timestamp: new Date().toISOString(),
      };
      setChatHistory((h) => [...h, entry]);
      setActiveInsightsEntry(entry);
      setLastQueriedDocId(selectedDocumentId);
      setTimeout(() => setLastQueriedDocId(null), 2000);
      setQuery("");
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleClearChat = () => {
    setChatHistory([]);
    setActiveInsightsEntry(null);
    clearMessages();
  };

  return (
    <div className="app-shell">
      <TopNav
        selectedDocument={selectedDocument}
        sidebarOpen={sidebarOpen}
        insightsPanelOpen={insightsPanelOpen}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        onToggleInsights={() => setInsightsPanelOpen((o) => !o)}
        hasChatHistory={chatHistory.length > 0}
        onClearChat={handleClearChat}
      />

      <StatusBanner error={errorMessage} success={successMessage} />

      <div className="app-body">
        <Sidebar
          open={sidebarOpen}
          documents={documents}
          selectedDocumentId={selectedDocumentId}
          lastQueriedDocId={lastQueriedDocId}
          onSelectDocument={handleSelectDocument}
          onRefreshDocuments={() => void loadDocuments()}
          onUpload={handleUpload}
          isLoading={isLoadingDocuments}
          isUploading={isUploading}
        />

        <div className="app-center">
          {isBootstrapping ? (
            <div style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 10,
              color: "var(--text-3)",
              fontSize: 13,
            }}>
              <span className="spin-icon" style={{ display: "flex" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
              </span>
              Loading…
            </div>
          ) : (
            <ChatWindow
              selectedDocument={selectedDocument}
              history={chatHistory}
              query={query}
              setQuery={setQuery}
              onSend={handleSend}
              isQuerying={isQuerying}
            />
          )}
        </div>

        <InsightsPanel
          open={insightsPanelOpen}
          entry={activeInsightsEntry}
        />
      </div>
    </div>
  );
}

export default App;
