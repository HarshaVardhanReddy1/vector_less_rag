import { FileText, Layers, RefreshCw, Search } from "lucide-react";
import { useState } from "react";
import UploadBox from "./UploadBox";

function Sidebar({
  open,
  documents,
  selectedDocumentId,
  onSelectDocument,
  onRefreshDocuments,
  onUpload,
  isLoading,
  isUploading,
}) {
  const [query, setQuery] = useState("");

  const filtered = documents.filter((d) =>
    d.document_name.toLowerCase().includes(query.toLowerCase())
  );

  const totalSections = documents.reduce((sum, d) => sum + (d.total_nodes || 0), 0);

  return (
    <aside className={`sidebar${open ? "" : " sidebar--collapsed"}`}>
      <div className="sidebar__inner">
        <div className="sidebar__head">
          <span className="sidebar__title">Library</span>
          <button
            className={`icon-btn${isLoading ? " spin-icon" : ""}`}
            onClick={onRefreshDocuments}
            disabled={isLoading}
            title="Refresh documents"
          >
            <RefreshCw size={13} className={isLoading ? "spin-icon" : ""} />
          </button>
        </div>

        <div className="sidebar__scroll">
          <UploadBox onUpload={onUpload} isUploading={isUploading} />

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div className="search-input">
              <Search size={12} className="search-input__icon" />
              <input
                placeholder="Search documents…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            <span className="section-label">
              {filtered.length} document{filtered.length !== 1 ? "s" : ""}
            </span>

            <div className="doc-list">
              {filtered.length ? (
                filtered.map((doc) => {
                  const active = selectedDocumentId === doc._id;
                  const status = (doc.status || "READY").toUpperCase();
                  return (
                    <button
                      key={doc._id}
                      className={`doc-card${active ? " doc-card--active" : ""}`}
                      onClick={() => onSelectDocument(doc._id)}
                      type="button"
                    >
                      <div className="doc-card__icon">
                        <FileText size={14} />
                      </div>
                      <div className="doc-card__info">
                        <div className="doc-card__name">{doc.document_name}</div>
                        <div className="doc-card__meta">
                          {doc.total_nodes || 0} sections indexed
                        </div>
                      </div>
                      <span
                        className={`status-dot-badge status-dot-badge--${
                          status === "READY" ? "ready" : "processing"
                        }`}
                      />
                    </button>
                  );
                })
              ) : (
                <div className="empty-lib">
                  <div className="empty-lib__icon">
                    <Layers size={18} />
                  </div>
                  <div className="empty-lib__title">
                    {query ? "No matches" : "No documents yet"}
                  </div>
                  <div className="empty-lib__sub">
                    {query ? "Try a different search term." : "Upload a PDF to get started."}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="sidebar__footer">
          <div className="sidebar-stat">
            <div className="sidebar-stat__value">{documents.length}</div>
            <div className="sidebar-stat__label">Documents</div>
          </div>
          <div className="sidebar-stat">
            <div className="sidebar-stat__value">{totalSections}</div>
            <div className="sidebar-stat__label">Sections</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
