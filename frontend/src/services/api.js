import axios from 'axios';

const configuredBaseURL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? 'https://lang-rag.onrender.com' : 'http://127.0.0.1:8000');
const baseURL = configuredBaseURL.replace(/\/+$/, '');
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
      if (!response.body) {
        throw new Error('The server did not provide an answer stream');
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let completed = false;
      const processEvent = (event) => {
        const data = event
          .split(/\r?\n/)
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trimStart())
          .join('\n');
        if (!data) return;

        let payload;
        try {
          payload = JSON.parse(data);
        } catch {
          throw new Error('The server returned an invalid answer response');
        }

        if (payload.type === 'sources' && onSources) onSources(payload.sources);
        if (payload.type === 'token' && onToken) onToken(payload.content);
        if (payload.type === 'error') {
          throw new Error(payload.detail || 'Could not generate an answer');
        }
        if (payload.type === 'done') {
          completed = true;
          if (onDone) onDone();
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          buffer += decoder.decode();
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || '';

        events.forEach(processEvent);
      }

      buffer.split(/\r?\n\r?\n/).forEach(processEvent);

      if (!completed) throw new Error('The answer stream ended unexpectedly');
    })
    .catch((err) => {
      if (err.name !== 'AbortError' && onError) onError(err);
    });

  return () => controller.abort();
}

export default client;
