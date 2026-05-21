import { useRef, useState } from "react";

function UploadBox({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const [selectedFileName, setSelectedFileName] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    setSelectedFileName(file?.name || "");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      return;
    }

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
        <label className="upload-box" htmlFor="document-upload">
          <input
            id="document-upload"
            ref={fileInputRef}
            type="file"
            name="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <span className="upload-box__title">Select a PDF file</span>
          <span className="upload-box__subtitle">
            {selectedFileName || "The file will be indexed for document chat."}
          </span>
        </label>

        <button className="button" type="submit" disabled={isUploading || !selectedFileName}>
          {isUploading ? "Uploading..." : "Upload PDF"}
        </button>
      </form>
    </section>
  );
}

export default UploadBox;
