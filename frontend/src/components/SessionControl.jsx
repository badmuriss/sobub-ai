import { useState, useEffect, useRef } from 'react';
import websocketService from '../services/websocket';
import apiService from '../services/api';

export default function SessionControl({ onTrigger }) {
  const [isActive, setIsActive] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [events, setEvents] = useState([]);
  const [showEventLog, setShowEventLog] = useState(() => {
    // Load preference from localStorage, default to true
    const saved = localStorage.getItem('showEventLog');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const eventsEndRef = useRef(null);

  const addEvent = (type, data) => {
    const event = {
      id: Date.now() + Math.random(),
      type,
      timestamp: new Date(),
      ...data
    };
    setEvents(prev => [...prev.slice(-19), event]); // Keep last 20 events
  };

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleEventLog = () => {
    const newValue = !showEventLog;
    setShowEventLog(newValue);
    localStorage.setItem('showEventLog', JSON.stringify(newValue));
  };

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  useEffect(() => {
    // Set up WebSocket callbacks
    websocketService.on('transcription', (text) => {
      addEvent('transcription', { text });
    });

    websocketService.on('match', (data) => {
      addEvent('match', {
        matched_tags: data.matched_tags,
        transcription: data.transcription
      });
    });

    websocketService.on('trigger', (data) => {
      addEvent('trigger', {
        filename: data.filename,
        matched_tags: data.matched_tags
      });
      if (onTrigger) {
        onTrigger(data);
      }
    });

    websocketService.on('debug', (data) => {
      addEvent('debug', {
        level: data.level,
        message: data.message
      });
    });

    websocketService.on('error', (err) => {
      setError('Connection error occurred');
      console.error(err);
      addEvent('error', { message: err.message || 'Connection error' });
    });

    websocketService.on('connectionChange', (connected) => {
      if (!connected && isActive) {
        setIsActive(false);
      }
    });

    // Load initial status
    loadStatus();

    // Cleanup function runs when component unmounts
    return () => {
      // Stop recording and disconnect WebSocket
      websocketService.stopRecording();
      websocketService.disconnect();
      console.log('SessionControl unmounted - session stopped');
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
      // Load settings to get chunk length
      const settings = await apiService.getSettings();
      const chunkLength = settings.chunk_length_seconds || 3;

      // Connect WebSocket
      await websocketService.connect();

      // Start recording with configured chunk length
      await websocketService.startRecording(chunkLength);

      setIsActive(true);
      setIsConnecting(false);
    } catch (err) {
      // Use the specific error message from the service
      setError(err.message || 'Failed to start session. Please check microphone permissions.');
      setIsConnecting(false);
      console.error(err);

      // Add error event to feed
      addEvent('error', { message: err.message });
    }
  };

  const handleStop = () => {
    websocketService.stopRecording();
    websocketService.disconnect();
    setIsActive(false);
    setEvents([]);
    setError(null);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderEvent = (event) => {
    const timeStr = event.timestamp.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    switch (event.type) {
      case 'transcription':
        return (
          <div key={event.id} className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-sm">
                🎤
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-blue-400 mb-1">{timeStr}</div>
                <div className="text-white italic">"{event.text}"</div>
              </div>
            </div>
          </div>
        );

      case 'match':
        return (
          <div key={event.id} className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-sm">
                🎯
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-yellow-400 mb-1">{timeStr} • Match Found</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {event.matched_tags.map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 bg-yellow-500/20 border border-yellow-500/50 rounded text-xs text-yellow-300">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'trigger':
        return (
          <div key={event.id} className="bg-green-900/20 border border-green-500/50 rounded-lg p-3 animate-pulse">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-sm">
                🔊
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-green-400 mb-1">{timeStr} • TRIGGERED!</div>
                <div className="text-green-300 font-semibold">{event.filename}</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {event.matched_tags.map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 bg-green-500/20 border border-green-500/50 rounded text-xs text-green-300">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'debug':
        const colors = {
          warning: 'orange',
          error: 'red',
          info: 'gray',
          cooldown: 'purple',
          probability: 'pink'
        };
        const color = colors[event.level] || 'gray';
        return (
          <div key={event.id} className={`bg-${color}-900/20 border border-${color}-500/30 rounded-lg p-2`}>
            <div className="flex items-center gap-2">
              <div className={`text-xs text-${color}-400`}>{timeStr}</div>
              <div className={`text-xs text-${color}-300`}>{event.message}</div>
            </div>
          </div>
        );

      case 'error':
        return (
          <div key={event.id} className="bg-red-900/30 border border-red-500/50 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-sm">
                ⚠️
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-red-400 mb-1">{timeStr} • Error</div>
                <div className="text-red-300">{event.message}</div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col items-center justify-start min-h-screen px-4 pt-20">
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

      {/* Status Indicator */}
      {isActive && (
        <div className="mt-6 flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium text-red-400">LISTENING</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-6 bg-red-900/20 border border-red-500 rounded-lg p-4 max-w-2xl">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!isActive && events.length === 0 && !error && (
        <p className="text-dark-muted mt-6 text-center">
          Tap the button to start listening
        </p>
      )}

      {/* Event Log Toggle */}
      {(events.length > 0 || isActive) && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <span className="text-sm text-dark-muted">Event Log</span>
          <button
            onClick={toggleEventLog}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              showEventLog ? 'bg-green-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                showEventLog ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      )}

      {/* Events Feed */}
      {showEventLog && events.length > 0 && (
        <div className="mt-4 w-full max-w-4xl">
          <div className="text-xs text-dark-muted mb-3 text-center">
            Real-time transcription and debug feed
          </div>
          <div className="space-y-3 max-h-[50vh] overflow-y-auto p-4 bg-dark-surface/50 rounded-lg border border-dark-border">
            {events.map(renderEvent)}
            <div ref={eventsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
