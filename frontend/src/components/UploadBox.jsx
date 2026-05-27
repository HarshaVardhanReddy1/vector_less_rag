import { useRef, useState } from "react";

function UploadBox({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const applyFile = (file) => {
    if (!file || file.type !== "application/pdf") return;
    setSelectedFileName(file.name);
    // Sync file to the hidden input so the form submit path still works
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInputRef.current.files = dt.files;
  };

  const handleFileChange = (event) => {
    applyFile(event.target.files?.[0]);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    applyFile(event.dataTransfer.files?.[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    await onUpload(file);
    event.target.reset();
    setSelectedFileName("");
  };

  return (
    <section className="upload-card">
      <div className="upload-card__header">
        <div>
          <p className="eyebrow">Upload</p>
          <h2>New PDF</h2>
        </div>
      </div>

      <form className="upload-card__form" onSubmit={handleSubmit}>
        <label
          className={`upload-box${isDragging ? " upload-box--dragging" : ""}`}
          htmlFor="document-upload"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            id="document-upload"
            ref={fileInputRef}
            type="file"
            name="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <span className="upload-box__icon">📄</span>
          <span className="upload-box__title">
            {isDragging ? "Drop it here!" : "Select or drag a PDF"}
          </span>
          <span className="upload-box__subtitle">
            {selectedFileName || "PDF files only · will be indexed for chat"}
          </span>
        </label>

        <button className="button" type="submit" disabled={isUploading || !selectedFileName}>
          {isUploading ? "Uploading…" : "Upload PDF"}
        </button>
      </form>
    </section>
  );
}

export default UploadBox;
