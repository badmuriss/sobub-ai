// Auto-detect WebSocket URL based on where the frontend is accessed from
// This allows mobile devices to automatically connect to the PC backend
const getWsUrl = () => {
  if (typeof window !== 'undefined') {
    // Use wss:// for HTTPS, ws:// for HTTP
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname; // localhost or 192.168.x.x
    return `${protocol}//${hostname}:8000`;
  }
  // Fallback for non-browser contexts (SSR, testing)
  return 'ws://localhost:8000';
};

const WS_URL = getWsUrl();

class WebSocketService {
  constructor() {
    this.ws = null;
    this.clientId = this.generateClientId();
    this.mediaRecorder = null;
    this.audioContext = null;
    this.isRecording = false;
    this.callbacks = {
      onTranscription: null,
      onTrigger: null,
      onError: null,
      onConnectionChange: null,
    };
  }

  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_URL}/ws/${this.clientId}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          if (this.callbacks.onConnectionChange) {
            this.callbacks.onConnectionChange(true);
          }
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (this.callbacks.onError) {
            this.callbacks.onError(error);
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          if (this.callbacks.onConnectionChange) {
            this.callbacks.onConnectionChange(false);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopRecording();
  }

  handleMessage(data) {
    switch (data.type) {
      case 'transcription':
        if (this.callbacks.onTranscription) {
          this.callbacks.onTranscription(data.text);
        }
        break;
      case 'trigger':
        if (this.callbacks.onTrigger) {
          this.callbacks.onTrigger(data);
        }
        break;
      case 'pong':
        // Handle ping/pong if needed
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  async startRecording() {
    if (this.isRecording) return;

    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });

      // Create MediaRecorder
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
          // Send audio chunk to backend
          event.data.arrayBuffer().then(buffer => {
            this.ws.send(buffer);
          });
        }
      };

      this.mediaRecorder.onerror = (error) => {
        console.error('MediaRecorder error:', error);
        if (this.callbacks.onError) {
          this.callbacks.onError(error);
        }
      };

      // Start recording with chunks every 3 seconds
      this.mediaRecorder.start(3000);
      this.isRecording = true;

      console.log('Recording started');
    } catch (error) {
      console.error('Failed to start recording:', error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
      throw error;
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      
      // Stop all tracks
      if (this.mediaRecorder.stream) {
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
      
      this.mediaRecorder = null;
      this.isRecording = false;
      
      console.log('Recording stopped');
    }
  }

  on(event, callback) {
    if (event === 'transcription') {
      this.callbacks.onTranscription = callback;
    } else if (event === 'trigger') {
      this.callbacks.onTrigger = callback;
    } else if (event === 'error') {
      this.callbacks.onError = callback;
    } else if (event === 'connectionChange') {
      this.callbacks.onConnectionChange = callback;
    }
  }

  sendControlMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  getStatus() {
    this.sendControlMessage({ type: 'get_status' });
  }
}

export default new WebSocketService();
