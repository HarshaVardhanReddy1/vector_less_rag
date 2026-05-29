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


export async function queryDocument({ documentId, query, evaluate = false }) {
  const params = new URLSearchParams({ query });
  if (evaluate) params.set("evaluate", "true");

  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/query?${params.toString()}`
  );
  return parseResponse(response);
}


export async function fetchDocumentStatus(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/status`);
  return parseResponse(response);
}


export async function queryDocumentStream(
  { documentId, query },
  { onMeta, onToken, onError, onDone } = {},
) {
  const params = new URLSearchParams({ query });
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/query/stream?${params.toString()}`,
  );

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data?.detail || "Stream request failed.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6);
      if (payload === "[DONE]") { onDone?.(); return; }
      try {
        const event = JSON.parse(payload);
        if (event.type === "meta") onMeta?.(event);
        else if (event.type === "token") onToken?.(event.content);
        else if (event.type === "error") onError?.(event.message);
      } catch { /* malformed chunk — skip */ }
    }
  }
  onDone?.();
}
