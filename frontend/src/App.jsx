import { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InsightsPanel from "./components/InsightsPanel";
import Sidebar from "./components/Sidebar";
import StatusBanner from "./components/StatusBanner";
import TopNav from "./components/TopNav";
import {
  fetchDocumentById,
  fetchDocumentStatus,
  listDocuments,
  queryDocumentStream,
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

  const pollUntilReady = async (documentId) => {
    const MAX_POLLS = 120;   // 10 minutes at 5 s intervals
    const INTERVAL_MS = 5000;

    for (let i = 0; i < MAX_POLLS; i++) {
      await new Promise((r) => setTimeout(r, INTERVAL_MS));
      try {
        const { status, error_message } = await fetchDocumentStatus(documentId);
        if (status === "READY") return { ok: true };
        if (status === "FAILED") return { ok: false, error: error_message || "Processing failed." };
      } catch {
        // transient network error — keep polling
      }
    }
    return { ok: false, error: "Processing timed out." };
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    clearMessages();
    try {
      const response = await uploadDocument(file);
      const docId = response.document_id;

      if (response.status === "PROCESSING") {
        setSuccessMessage("Upload received. Processing in the background…");
        const result = await pollUntilReady(docId);
        if (!result.ok) {
          setErrorMessage(result.error);
          setIsUploading(false);
          return;
        }
      }

      await loadDocuments(docId);
      setSuccessMessage(`Document indexed successfully.`);
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
    if (!selectedDocument?._id || selectedDocument?.status !== "READY") {
      setErrorMessage("Please select a ready document before asking a question.");
      return;
    }
    setIsQuerying(true);
    clearMessages();

    const entryIndex = { current: null };
    const entryData = {
      query: message,
      answer: "",
      selectedNodes: [],
      images: [],
      streaming: true,
      timestamp: new Date().toISOString(),
    };
    setChatHistory((h) => {
      entryIndex.current = h.length;
      return [...h, { ...entryData }];
    });
    setQuery("");

    // Mirror the accumulated entryData into chat history for rendering. We keep
    // a plain closure object as the source of truth so onDone can read the
    // final entry directly instead of relying on setState updater timing.
    const syncEntry = () => {
      setChatHistory((h) => {
        const idx = entryIndex.current;
        if (idx === null) return h;
        const updated = [...h];
        updated[idx] = { ...entryData };
        return updated;
      });
    };

    try {
      await queryDocumentStream(
        { documentId: selectedDocument._id, query: message },
        {
          onMeta: (event) => {
            entryData.selectedNodes = event.selected_nodes || [];
            syncEntry();
          },
          onToken: (token) => {
            entryData.answer += token;
            syncEntry();
          },
          onEval: (event) => {
            entryData.reasoning = event.reasoning;
            entryData.confidence = event.confidence;
            entryData.metrics = event.metrics;
            syncEntry();
          },
          onImages: (images) => {
            entryData.images = images;
            entryData.answer = entryData.answer
              .replace(/<REFERENCED_IMAGES>[\s\S]*?<\/REFERENCED_IMAGES>/g, "")
              .trimEnd();
            syncEntry();
          },
          onError: (message) => setErrorMessage(message),
          onDone: () => {
            entryData.streaming = false;
            syncEntry();
            setActiveInsightsEntry({ ...entryData });
            setLastQueriedDocId(selectedDocumentId);
            setTimeout(() => setLastQueriedDocId(null), 2000);
          },
        },
      );
    } catch (err) {
      setErrorMessage(err.message);
      entryData.streaming = false;
      syncEntry();
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
