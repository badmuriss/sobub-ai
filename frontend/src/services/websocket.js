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
    this.isAudioPlaying = false;
    this.corruptedChunksCount = 0;
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

    this.isAudioPlaying = false;

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const error = new Error(
          'Acesso ao microfone não disponível. ' +
          'A API getUserMedia requer HTTPS ou localhost. ' +
          'No celular, acesse via HTTPS ou use Chrome com a flag chrome://flags/#unsafely-treat-insecure-origin-as-secure'
        );
        error.name = 'NotSupportedError';
        throw error;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          suppressLocalAudioPlayback: true
        }
      });

      this.audioStream = stream;
      this.chunkLengthSeconds = chunkLengthSeconds;
      this.isRecording = true;

      this.startRecordingCycle();

      console.log(`Recording started (chunk length: ${chunkLengthSeconds}s)`);
    } catch (error) {
      console.error('Failed to start recording:', error);

      let errorMessage = error.message;

      if (error.name === 'NotAllowedError') {
        errorMessage = 'Permissão de microfone negada. Por favor, permita o acesso ao microfone nas configurações do navegador.';
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'Nenhum microfone encontrado. Verifique se seu dispositivo tem um microfone conectado.';
      } else if (error.name === 'NotSupportedError') {
        errorMessage = error.message;
      } else if (error.name === 'NotReadableError') {
        errorMessage = 'Microfone já está em uso por outro aplicativo. Feche outros apps que usam o microfone.';
      }

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

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      return;
    }

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
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const MIN_CHUNK_SIZE = 500;

        if (blob.size < MIN_CHUNK_SIZE) {
          this.corruptedChunksCount++;

          if (this.corruptedChunksCount >= 1) {
            await this.restartRecording();
            return;
          }
        } else {
          this.corruptedChunksCount = 0;
        }

        if (!this.isAudioPlaying && blob.size >= MIN_CHUNK_SIZE) {
          try {
            const buffer = await blob.arrayBuffer();
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(buffer);
            }
          } catch (error) {
            console.error('Failed to send audio chunk:', error);
          }
        }
      }

      if (this.isRecording && !this.isAudioPlaying) {
        setTimeout(() => this.startRecordingCycle(), 100);
      }
    };

    this.mediaRecorder.onerror = (error) => {
      console.error('MediaRecorder error:', error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
    };

    this.mediaRecorder.start();
    setTimeout(() => {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
    }, this.chunkLengthSeconds * 1000);
  }

  stopRecording() {
    this.isRecording = false;
    this.isAudioPlaying = false;
    this.corruptedChunksCount = 0;

    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }

    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
      this.audioStream = null;
    }

    this.mediaRecorder = null;

    console.log('Recording stopped');
  }

  async restartRecording() {
    const savedChunkLength = this.chunkLengthSeconds;

    this.stopRecording();

    await new Promise(resolve => setTimeout(resolve, 500));

    try {
      await this.startRecording(savedChunkLength);
    } catch (error) {
      console.error('Failed to restart recording:', error);

      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
    }
  }

  setAudioPlaying(isPlaying) {
    const wasPlaying = this.isAudioPlaying;
    this.isAudioPlaying = isPlaying;

    if (!wasPlaying && isPlaying) {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.stop();
      }
    }

    if (wasPlaying && !isPlaying) {
      if (this.isRecording) {
        setTimeout(() => {
          if (this.isRecording) {
            this.startRecordingCycle();
          }
        }, 100);
      }
    }
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
