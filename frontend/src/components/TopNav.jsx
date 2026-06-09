import { ChevronRight, Cpu, FileText, PanelLeftOpen, PanelRightOpen, Sparkles, Trash2 } from "lucide-react";

function TopNav({
  selectedDocument,
  sidebarOpen,
  insightsPanelOpen,
  onToggleSidebar,
  onToggleInsights,
  hasChatHistory,
  onClearChat,
}) {
  return (
    <header className="topnav">
      <div className="topnav__left">
        <button className="topnav__menu-btn" onClick={onToggleSidebar} title="Toggle sidebar">
          <PanelLeftOpen size={16} />
        </button>

        <div className="topnav__brand">
          <div className="topnav__brand-mark">
            <Sparkles size={13} color="#fff" />
          </div>
          <span className="topnav__brand-name">RAG Studio</span>
        </div>

        {selectedDocument && (
          <>
            <span className="topnav__sep"><ChevronRight size={13} /></span>
            <div className="topnav__doc-crumb">
              <FileText size={11} className="topnav__doc-icon" />
              <span className="topnav__doc-name">{selectedDocument.document_name}</span>
            </div>
          </>
        )}
      </div>

      <div className="topnav__right">
        <div className="badge-pill badge-pill--blue">
          <Cpu size={11} />
          <span>OpenRouter</span>
        </div>

        <div className="badge-pill badge-pill--emerald">
          <span className="live-dot" />
          Live
        </div>

        {hasChatHistory && (
          <button className="icon-btn" onClick={onClearChat} title="Clear conversation">
            <Trash2 size={14} />
          </button>
        )}

        <button
          className={`icon-btn${insightsPanelOpen ? " icon-btn--active" : ""}`}
          onClick={onToggleInsights}
          title="Toggle insights panel"
        >
          <PanelRightOpen size={15} />
        </button>
      </div>
    </header>
  );
}

export default TopNav;
