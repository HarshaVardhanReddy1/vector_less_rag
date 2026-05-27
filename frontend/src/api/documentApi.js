const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data?.detail || data?.message || "Request failed.";
    throw new Error(message);
  }

  return data;
}


export async function listDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`);
  return parseResponse(response);
}


export async function fetchDocumentById(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`);
  return parseResponse(response);
}


export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}


export async function queryDocument({ query, treePath, pagesPath }) {
  const params = new URLSearchParams({
    query,
    tree_path: treePath,
    pages_path: pagesPath,
  });

  const response = await fetch(`${API_BASE_URL}/documents/query?${params.toString()}`);
  return parseResponse(response);
}
