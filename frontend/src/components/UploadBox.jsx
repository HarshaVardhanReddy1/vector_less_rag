import { Loader2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

function UploadBox({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const applyFile = (file) => {
    if (!file || file.type !== "application/pdf") return;
    setSelectedFile(file);
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInputRef.current.files = dt.files;
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    applyFile(e.dataTransfer.files?.[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    await onUpload(file);
    e.target.reset();
    setSelectedFile(null);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
      <label
        className={`upload-zone${isDragging ? " upload-zone--dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          id="document-upload"
          type="file"
          name="file"
          accept="application/pdf"
          onChange={(e) => applyFile(e.target.files?.[0])}
          disabled={isUploading}
        />
        <div className="upload-zone__icon-wrap">
          <UploadCloud size={16} />
        </div>
        <span className="upload-zone__title">
          {isDragging ? "Drop PDF here" : "Upload PDF"}
        </span>
        {selectedFile ? (
          <span className="upload-zone__filename">{selectedFile.name}</span>
        ) : (
          <span className="upload-zone__sub">Drag & drop or click · PDF only</span>
        )}
      </label>

      <button
        className="btn btn--primary btn--full btn--sm"
        type="submit"
        disabled={isUploading || !selectedFile}
      >
        {isUploading ? (
          <>
            <Loader2 size={13} className="spin-icon" />
            Indexing…
          </>
        ) : (
          "Index document"
        )}
      </button>
    </form>
  );
}

export default UploadBox;
