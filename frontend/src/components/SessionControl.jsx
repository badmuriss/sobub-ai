import { useState, useEffect } from 'react';
import websocketService from '../services/websocket';
import apiService from '../services/api';

export default function SessionControl({ onTrigger }) {
  const [isActive, setIsActive] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastTranscription, setLastTranscription] = useState('');
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    // Set up WebSocket callbacks
    websocketService.on('transcription', (text) => {
      setLastTranscription(text);
    });

    websocketService.on('trigger', (data) => {
      if (onTrigger) {
        onTrigger(data);
      }
    });

    websocketService.on('error', (err) => {
      setError('Connection error occurred');
      console.error(err);
    });

    websocketService.on('connectionChange', (connected) => {
      if (!connected && isActive) {
        setIsActive(false);
      }
    });

    // Load initial status
    loadStatus();

    return () => {
      if (isActive) {
        handleStop();
      }
    };
  }, []);

  const loadStatus = async () => {
    try {
      const statusData = await apiService.getStatus();
      setStatus(statusData);
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  const handleStart = async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // Connect WebSocket
      await websocketService.connect();

      // Start recording
      await websocketService.startRecording();

      setIsActive(true);
      setIsConnecting(false);
    } catch (err) {
      setError('Failed to start session. Please check microphone permissions.');
      setIsConnecting(false);
      console.error(err);
    }
  };

  const handleStop = () => {
    websocketService.stopRecording();
    websocketService.disconnect();
    setIsActive(false);
    setLastTranscription('');
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      {/* Status Info */}
      {status && !isActive && (
        <div className="mb-8 text-center text-dark-muted text-sm">
          <p>Cooldown: {status.cooldown_seconds}s</p>
          <p>Trigger Probability: {status.trigger_probability}%</p>
          {status.cooldown_active && (
            <p className="text-yellow-500 mt-2">
              Cooldown active: {formatTime(status.cooldown_remaining)} remaining
            </p>
          )}
        </div>
      )}

      {/* Main Button */}
      <button
        onClick={isActive ? handleStop : handleStart}
        disabled={isConnecting}
        className={`
          w-48 h-48 rounded-full flex items-center justify-center
          text-2xl font-bold transition-all duration-300 transform
          ${isActive 
            ? 'bg-red-600 hover:bg-red-700 scale-110' 
            : 'bg-green-600 hover:bg-green-700 hover:scale-105'
          }
          ${isConnecting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          shadow-2xl
        `}
      >
        {isConnecting ? 'Starting...' : isActive ? 'Stop' : 'Start Session'}
      </button>

      {/* Status Messages */}
      <div className="mt-8 text-center max-w-md">
        {error && (
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 mb-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {isActive && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <p className="text-dark-muted">Listening...</p>
            </div>

            {lastTranscription && (
              <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
                <p className="text-sm text-dark-muted mb-1">Last heard:</p>
                <p className="text-dark-text italic">"{lastTranscription}"</p>
              </div>
            )}
          </div>
        )}

        {!isActive && !error && (
          <p className="text-dark-muted mt-4">
            Tap the button to start listening
          </p>
        )}
      </div>
    </div>
  );
}
