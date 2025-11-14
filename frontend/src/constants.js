/**
<<<<<<< HEAD
 * Constants and configuration for SOBUB AI Frontend
=======
 * Constants and configuration for Sobub AI Frontend
>>>>>>> 8a38096837c66815ff3d73c6d5cda79c89c6b57a
 *
 * This module centralizes all constants, magic numbers, and configuration
 * values to improve maintainability and eliminate magic strings/numbers.
 */

// ============================================================================
// Event Types
// ============================================================================

/**
 * Event type constants for WebSocket messages
 *
 * @readonly
 * @enum {string}
 */
export const EVENT_TYPES = {
  /** Audio transcription event */
  TRANSCRIPTION: 'transcription',
  /** Tag match event */
  MATCH: 'match',
  /** Meme trigger event */
  TRIGGER: 'trigger',
  /** Debug information event */
  DEBUG: 'debug',
  /** Error event */
  ERROR: 'error',
};

// ============================================================================
// Event Log Configuration
// ============================================================================

/**
 * Event log display configuration
 *
 * @typedef {Object} EventLogConfig
 * @property {number} MAX_EVENTS - Maximum number of events to keep in log
 * @property {boolean} SHOW_BY_DEFAULT - Whether to show event log by default
 * @property {string} STORAGE_KEY - LocalStorage key for event log visibility preference
 */
export const EVENT_LOG_CONFIG = {
  MAX_EVENTS: 20,
  SHOW_BY_DEFAULT: true,
  STORAGE_KEY: 'showEventLog',
};

// ============================================================================
// Audio Configuration
// ============================================================================

export const AUDIO_CONFIG = {
  // MediaRecorder settings
  SAMPLE_RATE: 16000, // 16kHz
  CHANNEL_COUNT: 1, // Mono
  MIME_TYPE: 'audio/webm;codecs=opus',

  // Audio capture settings
  ECHO_CANCELLATION: true,
  NOISE_SUPPRESSION: true,
  AUTO_GAIN_CONTROL: true,
  SUPPRESS_LOCAL_AUDIO: true,

  // Recording cycle
  RECORDING_RESTART_DELAY: 100, // ms delay between recording cycles
};

// ============================================================================
// API Configuration
// ============================================================================

/**
 * API configuration and endpoints
 */
export const API_CONFIG = {
  /**
   * Dynamically detect base URL from current window location.
   * Works for both localhost and remote IP addresses (mobile support).
   *
   * @returns {string} Base URL (e.g., "https://localhost" or "http://192.168.1.100")
   */
  getBaseUrl() {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      return `${protocol}//${hostname}`;
    }
    return 'http://localhost';
  },

  /**
   * API endpoint paths
   * @readonly
   */
  ENDPOINTS: {
    MEMES: '/api/memes',
    SETTINGS: '/api/settings',
    STATUS: '/api/status',
    TAGS: '/api/tags',
    AUDIO: '/audio',
  },
};

// ============================================================================
// WebSocket Configuration
// ============================================================================

/**
 * WebSocket connection configuration
 */
export const WEBSOCKET_CONFIG = {
  /**
   * Build WebSocket URL from current location and client ID.
   * Automatically uses wss:// for HTTPS and ws:// for HTTP.
   *
   * @param {string} clientId - Unique client identifier
   * @returns {string} WebSocket URL (e.g., "wss://localhost/ws/client_123")
   */
  getUrl(clientId) {
    const baseUrl = API_CONFIG.getBaseUrl();
    const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
    const hostname = baseUrl.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${hostname}/ws/${clientId}`;
  },

  /** Delay before reconnection attempt (milliseconds) */
  RECONNECT_DELAY: 3000,
  /** Heartbeat interval to keep connection alive (milliseconds) */
  HEARTBEAT_INTERVAL: 30000,
  /** Maximum number of reconnection attempts before giving up */
  MAX_RECONNECT_ATTEMPTS: 5,
};

// ============================================================================
// Color Schemes (Tailwind-safe)
// ============================================================================

export const EVENT_COLORS = {
  transcription: {
    bg: 'bg-blue-900/20',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    icon: 'text-blue-500',
  },
  match: {
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
    icon: 'text-yellow-500',
  },
  trigger: {
    bg: 'bg-green-900/20',
    border: 'border-green-500/30',
    text: 'text-green-400',
    icon: 'text-green-500',
  },
  debug: {
    bg: 'bg-gray-900/20',
    border: 'border-gray-500/30',
    text: 'text-gray-400',
    icon: 'text-gray-500',
  },
  error: {
    bg: 'bg-red-900/20',
    border: 'border-red-500/30',
    text: 'text-red-400',
    icon: 'text-red-500',
  },
};

// Debug level colors (for debug events)
export const DEBUG_LEVEL_COLORS = {
  info: {
    bg: 'bg-gray-900/20',
    border: 'border-gray-500/30',
    text: 'text-gray-400',
  },
  warning: {
    bg: 'bg-orange-900/20',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  error: {
    bg: 'bg-red-900/20',
    border: 'border-red-500/30',
    text: 'text-red-400',
  },
};

// ============================================================================
// Event Icons
// ============================================================================

export const EVENT_ICONS = {
  transcription: '🎤',
  match: '🎯',
  trigger: '🔊',
  debug: '🔧',
  error: '❌',
};

// ============================================================================
// Settings Configuration
// ============================================================================

export const SETTINGS_CONFIG = {
  // Validation ranges
  COOLDOWN: {
    MIN: 0,
    MAX: 60, // minutes
    DEFAULT: 3,
    STEP: 1,
  },
  PROBABILITY: {
    MIN: 0,
    MAX: 100,
    DEFAULT: 50,
    STEP: 1,
  },
  CHUNK_LENGTH: {
    MIN: 1,
    MAX: 30,
    DEFAULT: 3,
    STEP: 1,
  },

  // Available models
  WHISPER_MODELS: ['tiny', 'base', 'small', 'medium', 'large'],

  // Available languages
  LANGUAGES: [
    { code: 'en', name: 'English' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' },
  ],
};

// ============================================================================
// Meme Library Configuration
// ============================================================================

export const LIBRARY_CONFIG = {
  // File validation
  ALLOWED_FILE_TYPES: ['audio/mpeg', 'audio/mp3'],
  ALLOWED_EXTENSIONS: ['.mp3'],
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB

  // Tag validation
  MIN_TAG_LENGTH: 1,
  MAX_TAG_LENGTH: 50,
  MAX_TAGS_PER_MEME: 20,

  // Bulk upload
  MAX_BULK_UPLOAD: 50,

  // UI
  SEARCH_DEBOUNCE: 300, // ms
};

// ============================================================================
// UI Messages
// ============================================================================

export const MESSAGES = {
  // Success messages
  SUCCESS: {
    MEME_UPLOADED: 'Meme uploaded successfully!',
    MEME_UPDATED: 'Meme updated successfully!',
    MEME_DELETED: 'Meme deleted successfully!',
    SETTINGS_SAVED: 'Settings saved successfully!',
    SESSION_STARTED: 'Session started successfully!',
    SESSION_STOPPED: 'Session stopped.',
  },

  // Error messages
  ERROR: {
    MICROPHONE_DENIED: 'Microphone access denied. Please allow microphone access and try again.',
    MICROPHONE_ERROR: 'Failed to access microphone. Make sure you\'re using HTTPS.',
    CONNECTION_FAILED: 'Failed to connect to server. Please try again.',
    FILE_TOO_LARGE: 'File is too large. Maximum size is 50MB.',
    INVALID_FILE_TYPE: 'Invalid file type. Only MP3 files are allowed.',
    UPLOAD_FAILED: 'Failed to upload meme. Please try again.',
    DELETE_FAILED: 'Failed to delete meme. Please try again.',
    SETTINGS_FAILED: 'Failed to save settings. Please try again.',
    NO_TAGS: 'Please add at least one tag.',
    INVALID_TAGS: 'Tags must be 1-50 characters long.',
  },

  // Info messages
  INFO: {
    NO_MEMES: 'No memes found. Upload some to get started!',
    NO_MATCHES: 'No memes match your search.',
    LOADING: 'Loading...',
    CONNECTING: 'Connecting...',
  },
};

// ============================================================================
// Routes
// ============================================================================

export const ROUTES = {
  HOME: '/',
  SETTINGS: '/settings',
  LIBRARY: '/library',
};

// ============================================================================
// LocalStorage Keys
// ============================================================================

export const STORAGE_KEYS = {
  SHOW_EVENT_LOG: 'showEventLog',
  LAST_SESSION_SETTINGS: 'lastSessionSettings',
  USER_PREFERENCES: 'userPreferences',
};

// ============================================================================
// Timeouts & Delays
// ============================================================================

export const TIMEOUTS = {
  MESSAGE_DISPLAY: 3000, // ms to show success/error messages
  DEBOUNCE_SEARCH: 300, // ms to debounce search input
  RECONNECT_DELAY: 3000, // ms before websocket reconnect
  API_TIMEOUT: 30000, // ms for API requests
};

// ============================================================================
// Control Message Types
// ============================================================================

export const CONTROL_MESSAGE_TYPES = {
  AUDIO_ENDED: 'audio_ended',
  PAUSE_MIC: 'pause_mic',
  RESUME_MIC: 'resume_mic',
};

// ============================================================================
// Feature Flags
// ============================================================================

export const FEATURE_FLAGS = {
  ENABLE_EVENT_LOG: true,
  ENABLE_BULK_UPLOAD: true,
  ENABLE_SEARCH: true,
  ENABLE_AUDIO_PREVIEW: true,
  ENABLE_TAG_SUGGESTIONS: false, // Future feature
};
