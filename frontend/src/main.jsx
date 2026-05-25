import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';
import App from './App';
import { ChatProvider } from './context/ChatContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChatProvider>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#161b26',
            color: '#e5e7eb',
            border: '1px solid #2a3142',
          },
        }}
      />
    </ChatProvider>
  </React.StrictMode>
);
