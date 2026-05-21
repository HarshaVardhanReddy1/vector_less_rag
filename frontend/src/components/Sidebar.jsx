import UploadBox from "./UploadBox";

function Sidebar({
  documents,
  selectedDocumentId,
  onSelectDocument,
  onRefreshDocuments,
  onUpload,
  isLoading,
  isUploading,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="eyebrow">Documents</p>
          <h1>Indexed library</h1>
        </div>
        <button
          className="button button--ghost"
          type="button"
          onClick={onRefreshDocuments}
          disabled={isLoading}
        >
          Refresh
        </button>
      </div>

      <div className="sidebar__content">
        <UploadBox onUpload={onUpload} isUploading={isUploading} />

        <div className="document-list-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Choose one</p>
              <h2>Indexed documents</h2>
            </div>
          </div>

          <div className="document-list">
            {documents.length ? (
              documents.map((document) => {
                const isSelected = selectedDocumentId === document._id;

                return (
                  <button
                    key={document._id}
                    className={`document-item${isSelected ? " document-item--active" : ""}`}
                    type="button"
                    onClick={() => onSelectDocument(document._id)}
                  >
                    <div>
                      <strong>{document.document_name}</strong>
                      <span>{document.total_pages || 0} pages</span>
                    </div>
                    <span className="status-pill">{document.status || "READY"}</span>
                  </button>
                );
              })
            ) : (
              <div className="empty-state">
                <p>No indexed documents yet.</p>
                <span>Upload a PDF to start chatting with your content.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
