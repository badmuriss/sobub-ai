import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import SessionControl from './components/SessionControl';
import Settings from './components/Settings';
import AudioPlayer from './components/AudioPlayer';
import websocketService from './services/websocket';

function Navigation() {
  const location = useLocation();

  return (
    <nav className="bg-dark-surface border-b border-dark-border">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-dark-text">Sobub AI</h1>
          </div>
          <div className="flex gap-4">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === '/'
                  ? 'bg-green-600 text-white'
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              Home
            </Link>
            <Link
              to="/settings"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                location.pathname === '/settings'
                  ? 'bg-green-600 text-white'
                  : 'text-dark-muted hover:text-dark-text'
              }`}
            >
              Settings
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

function AppContent() {
  const [triggerData, setTriggerData] = useState(null);
  const [showNotification, setShowNotification] = useState(false);

  const handleTrigger = (data) => {
    setTriggerData(data);
    setShowNotification(true);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
      setShowNotification(false);
    }, 3000);
  };

  const handlePlayStart = () => {
    // Pause microphone sending while audio plays
    websocketService.setAudioPlaying(true);
  };

  const handlePlayEnd = () => {
    // Resume microphone sending
    websocketService.setAudioPlaying(false);

    // Notify backend that audio ended (to start cooldown)
    websocketService.sendControlMessage({ type: 'audio_ended' });
  };

  const handlePlayComplete = () => {
    // Optional: Do something when audio finishes playing
  };

  return (
    <div className="min-h-screen bg-dark-bg text-dark-text">
      <Navigation />
      
      {/* Notification */}
      {showNotification && triggerData && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in">
          <div className="bg-green-900/90 border border-green-500 rounded-lg px-6 py-3 shadow-2xl">
            <p className="text-white font-medium">
              🎵 Playing: {triggerData.filename}
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {triggerData.matched_tags?.map((tag, idx) => (
                <span
                  key={idx}
                  className="bg-green-700 text-white px-2 py-0.5 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <Routes>
        <Route path="/" element={<SessionControl onTrigger={handleTrigger} />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>

      {/* Audio Player */}
      <AudioPlayer
        triggerData={triggerData}
        onPlayStart={handlePlayStart}
        onPlayEnd={handlePlayEnd}
        onPlayComplete={handlePlayComplete}
      />
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}
