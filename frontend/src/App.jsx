import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import SettingsModal from './components/SettingsModal';
import ChatPage from './pages/ChatPage';

export default function App() {
  return (
    <div className="relative flex h-full min-h-screen bg-surface bg-gradient-radial">
      <Sidebar />
      <main className="flex flex-1 flex-col md:ml-0">
        <Navbar />
        <ChatPage />
      </main>
      <SettingsModal />
    </div>
  );
}
