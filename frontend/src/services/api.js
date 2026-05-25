import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL,
  timeout: 120000,
});

export async function checkHealth() {
  const { data } = await client.get('/health');
  return data;
}

export async function uploadFiles(files, onProgress) {
  const form = new FormData();
  files.forEach((file) => form.append('files', file));

  const { data } = await client.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}

export async function listDocuments() {
  const { data } = await client.get('/documents');
  return data.documents;
}

export async function deleteDocument(id) {
  const { data } = await client.delete(`/documents/${id}`);
  return data;
}

export async function askQuestion(question, history = []) {
  const { data } = await client.post('/ask', {
    question,
    history,
    stream: false,
  });
  return data;
}

/**
 * Stream answer via SSE. Calls onSources, onToken, onDone, onError.
 */
export function askQuestionStream(question, history, { onSources, onToken, onDone, onError }) {
  const url = `${baseURL}/ask/stream`;
  const controller = new AbortController();

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history, stream: true }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Stream failed: ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.type === 'sources' && onSources) onSources(payload.sources);
            if (payload.type === 'token' && onToken) onToken(payload.content);
            if (payload.type === 'done' && onDone) onDone();
          } catch {
            /* ignore malformed chunks */
          }
        }
      }
      if (onDone) onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError' && onError) onError(err);
    });

  return () => controller.abort();
}

export default client;
