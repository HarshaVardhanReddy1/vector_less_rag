import { useEffect, useState } from "react";

import DocumentSidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import StatusBanner from "./components/StatusBanner";
import Loader from "./components/Loader";
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

  const loadDocuments = async (preferredDocumentId) => {
    setIsLoadingDocuments(true);
    setErrorMessage("");

    try {
      const data = await listDocuments();
      const nextDocuments = data.documents || [];
      setDocuments(nextDocuments);

      const nextSelectedId =
        preferredDocumentId ||
        (nextDocuments.some((document) => document._id === selectedDocumentId)
          ? selectedDocumentId
          : nextDocuments[0]?._id || "");

      setSelectedDocumentId(nextSelectedId);
      return nextSelectedId;
    } catch (error) {
      setErrorMessage(error.message);
      return "";
    } finally {
      setIsLoadingDocuments(false);
      setIsBootstrapping(false);
    }
  };

  useEffect(() => {
    void loadDocuments();
  }, []);

  useEffect(() => {
    if (!selectedDocumentId) {
      setSelectedDocument(null);
      return;
    }

    let active = true;

    const loadSelectedDocument = async () => {
      try {
        const document = await fetchDocumentById(selectedDocumentId);
        if (active) {
          setSelectedDocument(document);
          setErrorMessage("");
        }
      } catch (error) {
        if (active) {
          setSelectedDocument(null);
          setErrorMessage(error.message);
        }
      }
    };

    void loadSelectedDocument();

    return () => {
      active = false;
    };
  }, [selectedDocumentId]);

  const handleUpload = async (file) => {
    setIsUploading(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await uploadDocument(file);
      await loadDocuments(response.document_id);
      setSuccessMessage(`Uploaded ${response.document_name} successfully.`);
      setChatHistory([]);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSelectDocument = (documentId) => {
    setSelectedDocumentId(documentId);
    setChatHistory([]);
    setErrorMessage("");
    setSuccessMessage("");
  };

  const handleSend = async (message) => {
    if (!selectedDocument?.tree_json_path || !selectedDocument?.nodes_json_path) {
      setErrorMessage("Please select a valid indexed document before asking a question.");
      return;
    }

    setIsQuerying(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await queryDocument({
        query: message,
        treePath: selectedDocument.tree_json_path,
        nodesPath: selectedDocument.nodes_json_path,
      });

      setChatHistory((history) => [
        ...history,
        {
          query: message,
          answer: response.answer,
          selectedNode: response.selected_node,
          reasoning: response.reasoning || "",
          confidence: response.confidence || "",
          metrics: response.metrics || {},
        },
      ]);
      setQuery("");
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="app-shell">
      <DocumentSidebar
        documents={documents}
        selectedDocumentId={selectedDocumentId}
        onSelectDocument={handleSelectDocument}
        onRefreshDocuments={() => void loadDocuments()}
        onUpload={handleUpload}
        isLoading={isLoadingDocuments}
        isUploading={isUploading}
      />

      <main className="app-main">
        <div className="main-heading">
          <div>
            <p className="eyebrow">Document chatbot</p>
            <h1>Ask your indexed content</h1>
          </div>
          <div className="main-stats">
            <div>
              <strong>{documents.length}</strong>
              <span>Indexed docs</span>
            </div>
            <div>
              <strong>{selectedDocument?.total_nodes || 0}</strong>
              <span>Sections indexed</span>
            </div>
          </div>
        </div>

        <div className="main-body">
          <StatusBanner error={errorMessage} success={successMessage} />

          {isBootstrapping ? (
            <div className="full-loader">
              <Loader label="Loading indexed documents..." />
            </div>
          ) : (
            <ChatWindow
              selectedDocument={selectedDocument}
              history={chatHistory}
              query={query}
              setQuery={setQuery}
              onSend={handleSend}
              isQuerying={isQuerying}
              onClearChat={() => setChatHistory([])}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
