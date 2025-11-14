// Auto-detect WebSocket URL based on where the frontend is accessed from
// With nginx reverse proxy, WebSocket is served from the same origin
const getWsUrl = () => {
  if (typeof window !== 'undefined') {
    // Use wss:// for HTTPS, ws:// for HTTP
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // includes port if any
    return `${protocol}//${host}`;
  }
  // Fallback for non-browser contexts (SSR, testing)
  return 'ws://localhost';
};

const WS_URL = getWsUrl();

class WebSocketService {
  constructor() {
    this.ws = null;
    this.clientId = this.generateClientId();
    this.mediaRecorder = null;
    this.audioStream = null;
    this.chunkLengthSeconds = 3;
    this.isRecording = false;
    this.isAudioPlaying = false; // Flag to pause sending while meme audio plays
    this.callbacks = {
      onTranscription: null,
      onMatch: null,
      onTrigger: null,
      onDebug: null,
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
      case 'match':
        if (this.callbacks.onMatch) {
          this.callbacks.onMatch(data);
        }
        break;
      case 'trigger':
        if (this.callbacks.onTrigger) {
          this.callbacks.onTrigger(data);
        }
        break;
      case 'debug':
        if (this.callbacks.onDebug) {
          this.callbacks.onDebug(data);
        }
        break;
      case 'pong':
        // Handle ping/pong if needed
        break;
      default:
        console.warn('Unknown message type:', data.type);
    }
  }

  async startRecording(chunkLengthSeconds = 3) {
    if (this.isRecording) return;

    // Reset audio playing flag when starting a new session
    this.isAudioPlaying = false;

    try {
      // Check if getUserMedia is available (requires HTTPS or localhost)
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const error = new Error(
          'Acesso ao microfone não disponível. ' +
          'A API getUserMedia requer HTTPS ou localhost. ' +
          'No celular, acesse via HTTPS ou use Chrome com a flag chrome://flags/#unsafely-treat-insecure-origin-as-secure'
        );
        error.name = 'NotSupportedError';
        throw error;
      }

      // Request microphone access with optimized settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Prevent audio playback from being captured
          suppressLocalAudioPlayback: true
        }
      });

      this.audioStream = stream;
      this.chunkLengthSeconds = chunkLengthSeconds;
      this.isRecording = true;

      // Start the recording cycle
      this.startRecordingCycle();

      console.log(`Recording started (chunk length: ${chunkLengthSeconds}s)`);
    } catch (error) {
      console.error('Failed to start recording:', error);

      // Provide user-friendly error messages
      let errorMessage = error.message;

      if (error.name === 'NotAllowedError') {
        errorMessage = 'Permissão de microfone negada. Por favor, permita o acesso ao microfone nas configurações do navegador.';
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'Nenhum microfone encontrado. Verifique se seu dispositivo tem um microfone conectado.';
      } else if (error.name === 'NotSupportedError') {
        errorMessage = error.message; // Use the detailed message from above
      } else if (error.name === 'NotReadableError') {
        errorMessage = 'Microfone já está em uso por outro aplicativo. Feche outros apps que usam o microfone.';
      }

      // Create enhanced error object
      const enhancedError = new Error(errorMessage);
      enhancedError.name = error.name;
      enhancedError.originalError = error;

      if (this.callbacks.onError) {
        this.callbacks.onError(enhancedError);
      }
      throw enhancedError;
    }
  }

  startRecordingCycle() {
    if (!this.isRecording || !this.audioStream) return;

    // Create a new MediaRecorder for each chunk to ensure complete WebM files
    this.mediaRecorder = new MediaRecorder(this.audioStream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    const chunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = async () => {
      if (chunks.length > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
        // Combine chunks into a single blob
        const blob = new Blob(chunks, { type: 'audio/webm' });

        // Only send if audio is not currently playing
        if (!this.isAudioPlaying) {
          try {
            // Wait for buffer conversion and send
            const buffer = await blob.arrayBuffer();
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(buffer);
            }
          } catch (error) {
            console.error('Failed to send audio chunk:', error);
          }
        } else {
          console.log('Skipping chunk send - meme audio is playing');
        }
      }

      // Start next recording cycle if still recording
      // Only after the current chunk has been fully processed and sent
      if (this.isRecording) {
        setTimeout(() => this.startRecordingCycle(), 100); // Small delay to prevent overlap
      }
    };

    this.mediaRecorder.onerror = (error) => {
      console.error('MediaRecorder error:', error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
    };

    // Record for the specified duration, then stop (creates complete WebM file)
    this.mediaRecorder.start();
    setTimeout(() => {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
    }, this.chunkLengthSeconds * 1000);
  }

  stopRecording() {
    this.isRecording = false;
    this.isAudioPlaying = false; // Reset flag when stopping

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }

    // Stop all tracks
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }

    this.mediaRecorder = null;

    console.log('Recording stopped');
  }

  setAudioPlaying(isPlaying) {
    console.log(`[DEBUG] setAudioPlaying called: ${this.isAudioPlaying} → ${isPlaying}`);
    this.isAudioPlaying = isPlaying;
    console.log(`Audio playback state: ${isPlaying ? 'playing' : 'stopped'} - mic sending ${isPlaying ? 'paused' : 'active'}`);
  }

  on(event, callback) {
    if (event === 'transcription') {
      this.callbacks.onTranscription = callback;
    } else if (event === 'match') {
      this.callbacks.onMatch = callback;
    } else if (event === 'trigger') {
      this.callbacks.onTrigger = callback;
    } else if (event === 'debug') {
      this.callbacks.onDebug = callback;
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
