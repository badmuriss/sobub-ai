import { useState, useEffect } from 'react';
import apiService from '../services/api';
import MemeLibrary from './MemeLibrary';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await apiService.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      await apiService.updateSettings({
        cooldown_seconds: parseInt(settings.cooldown_seconds),
        trigger_probability: parseFloat(settings.trigger_probability),
        chunk_length_seconds: parseInt(settings.chunk_length_seconds),
        language: settings.language,
        whisper_model: settings.whisper_model,
        use_stemming: settings.use_stemming === 'true' || settings.use_stemming === true ? 'true' : 'false',
      });
      setMessage({ type: 'success', text: 'Settings saved successfully' });
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  if (loading || !settings) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-dark-muted">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      {/* Settings Form */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-6">Configuration</h2>

        {/* Cooldown */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Cooldown Period (seconds)
          </label>
          <input
            type="number"
            value={settings.cooldown_seconds}
            onChange={(e) => handleChange('cooldown_seconds', e.target.value)}
            min="0"
            max="3600"
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <p className="text-sm text-dark-muted mt-1">
            Time between audio plays ({Math.floor(settings.cooldown_seconds / 60)} minutes)
          </p>
        </div>

        {/* Audio Chunk Length */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Audio Chunk Length (seconds)
          </label>
          <input
            type="number"
            value={settings.chunk_length_seconds}
            onChange={(e) => handleChange('chunk_length_seconds', e.target.value)}
            min="1"
            max="10"
            step="0.5"
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <p className="text-sm text-dark-muted mt-1">
            Duration of each audio recording chunk sent for transcription
          </p>
        </div>

        {/* Language */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Transcription Language
          </label>
          <select
            value={settings.language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="en">English</option>
            <option value="es">Español (Spanish)</option>
            <option value="pt">Português (Portuguese)</option>
          </select>
          <p className="text-sm text-dark-muted mt-1">
            Language for speech recognition
          </p>
        </div>

        {/* Use Stemming */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">
                Word Stemming
              </label>
              <p className="text-sm text-dark-muted">
                Match word variations (e.g., "running" matches "run", "played" matches "play")
              </p>
            </div>
            <button
              onClick={() => handleChange('use_stemming', settings.use_stemming === 'true' || settings.use_stemming === true ? 'false' : 'true')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.use_stemming === 'true' || settings.use_stemming === true ? 'bg-green-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.use_stemming === 'true' || settings.use_stemming === true ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Whisper Model */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Whisper Model
          </label>
          <select
            value={settings.whisper_model}
            onChange={(e) => handleChange('whisper_model', e.target.value)}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="tiny">Tiny (fastest, least accurate)</option>
            <option value="base">Base (balanced - recommended)</option>
            <option value="small">Small (slower, more accurate)</option>
            <option value="medium">Medium (very slow, very accurate)</option>
            <option value="large">Large (slowest, most accurate)</option>
          </select>
          <p className="text-sm text-dark-muted mt-1">
            Trade-off between speed and accuracy. Model will reload on next transcription.
          </p>
        </div>

        {/* Trigger Probability */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Trigger Probability (%)
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              value={settings.trigger_probability}
              onChange={(e) => handleChange('trigger_probability', e.target.value)}
              min="0"
              max="100"
              step="5"
              className="flex-1"
            />
            <span className="text-lg font-semibold w-16 text-right">
              {settings.trigger_probability}%
            </span>
          </div>
          <p className="text-sm text-dark-muted mt-1">
            Chance of playing audio when context matches
          </p>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-dark-border disabled:cursor-not-allowed rounded-lg py-3 font-semibold transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>

        {/* Message */}
        {message && (
          <div className={`mt-4 p-3 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-900/20 border border-green-500 text-green-400' 
              : 'bg-red-900/20 border border-red-500 text-red-400'
          }`}>
            {message.text}
          </div>
        )}
      </div>

      {/* Meme Library */}
      <MemeLibrary />
    </div>
  );
}
