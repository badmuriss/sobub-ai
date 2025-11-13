import { useState, useEffect } from 'react';
import apiService from '../services/api';

// TagInput Component with badge system (space-separated)
function TagInput({ tags, onChange, placeholder }) {
  const [currentInput, setCurrentInput] = useState('');

  const handleKeyDown = (e) => {
    if ((e.key === ',' || e.key === 'Enter') && currentInput.trim()) {
      e.preventDefault();
      const newTag = currentInput.trim();
      if (!tags.includes(newTag)) {
        onChange([...tags, newTag]);
      }
      setCurrentInput('');
    } else if (e.key === 'Backspace' && !currentInput && tags.length > 0) {
      // Delete last tag on backspace if input is empty
      onChange(tags.slice(0, -1));
    }
  };

  const handleChange = (e) => {
    const value = e.target.value;
    // If user types comma, create tag from what's before comma
    if (value.includes(',')) {
      const parts = value.split(',');
      const newTag = parts[0].trim();
      if (newTag && !tags.includes(newTag)) {
        onChange([...tags, newTag]);
      }
      // Keep any text after comma as new input
      setCurrentInput(parts.slice(1).join(','));
    } else {
      setCurrentInput(value);
    }
  };

  const removeTag = (indexToRemove) => {
    onChange(tags.filter((_, index) => index !== indexToRemove));
  };

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={currentInput}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Type tag and press comma or enter...'}
        className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
      />
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 bg-green-900/30 text-green-400 px-3 py-1 rounded-full text-sm border border-green-500/30"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(index)}
                className="hover:text-green-300 transition-colors"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MemeLibrary() {
  const [memes, setMemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editTags, setEditTags] = useState([]);
  const [message, setMessage] = useState(null);

  // Bulk upload staging state
  const [stagingMode, setStagingMode] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });

  useEffect(() => {
    loadMemes();
  }, []);

  useEffect(() => {
    // Cleanup blob URLs when component unmounts or staging mode exits
    return () => {
      pendingFiles.forEach(file => {
        if (file.audioUrl) {
          URL.revokeObjectURL(file.audioUrl);
        }
      });
    };
  }, [pendingFiles]);

  const loadMemes = async () => {
    try {
      const data = await apiService.getMemes();
      setMemes(data);
    } catch (error) {
      console.error('Failed to load memes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const newPendingFiles = files.map((file, index) => ({
      id: Date.now() + index,
      file: file,
      filename: file.name.replace('.mp3', ''),
      tags: [],
      audioUrl: URL.createObjectURL(file),
    }));

    setPendingFiles(newPendingFiles);
    setStagingMode(true);
    setMessage(null);

    // Reset file input
    e.target.value = '';
  };

  const updatePendingFile = (id, updates) => {
    setPendingFiles(prev =>
      prev.map(file => file.id === id ? { ...file, ...updates } : file)
    );
  };

  const removePendingFile = (id) => {
    const fileToRemove = pendingFiles.find(f => f.id === id);
    if (fileToRemove && fileToRemove.audioUrl) {
      URL.revokeObjectURL(fileToRemove.audioUrl);
    }
    setPendingFiles(prev => prev.filter(file => file.id !== id));

    // Exit staging mode if no files left
    if (pendingFiles.length === 1) {
      cancelStaging();
    }
  };

  const cancelStaging = () => {
    // Cleanup blob URLs
    pendingFiles.forEach(file => {
      if (file.audioUrl) {
        URL.revokeObjectURL(file.audioUrl);
      }
    });
    setPendingFiles([]);
    setStagingMode(false);
    setMessage(null);
  };

  const confirmBulkUpload = async () => {
    // Validate all files have at least one tag
    const filesWithoutTags = pendingFiles.filter(f => f.tags.length === 0);
    if (filesWithoutTags.length > 0) {
      setMessage({
        type: 'error',
        text: `${filesWithoutTags.length} file(s) missing tags. Please add at least one tag to each file.`
      });
      return;
    }

    setUploading(true);
    setUploadProgress({ current: 0, total: pendingFiles.length });
    const errors = [];

    for (let i = 0; i < pendingFiles.length; i++) {
      const pending = pendingFiles[i];
      setUploadProgress({ current: i + 1, total: pendingFiles.length });

      try {
        // Rename file to user's chosen filename
        const newFileName = `${pending.filename}.mp3`;
        const renamedFile = new File([pending.file], newFileName, { type: pending.file.type });

        await apiService.createMeme(renamedFile, pending.tags);
      } catch (error) {
        console.error(`Failed to upload ${pending.filename}:`, error);
        errors.push(pending.filename);
      }
    }

    // Cleanup
    pendingFiles.forEach(file => {
      if (file.audioUrl) {
        URL.revokeObjectURL(file.audioUrl);
      }
    });

    setUploading(false);
    setPendingFiles([]);
    setStagingMode(false);

    // Show result message
    if (errors.length === 0) {
      setMessage({
        type: 'success',
        text: `Successfully uploaded ${pendingFiles.length} audio file(s)`
      });
    } else {
      setMessage({
        type: 'error',
        text: `Uploaded ${pendingFiles.length - errors.length} files. Failed: ${errors.join(', ')}`
      });
    }

    await loadMemes();
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this audio?')) return;

    try {
      await apiService.deleteMeme(id);
      setMessage({ type: 'success', text: 'Audio deleted successfully' });
      await loadMemes();
    } catch (error) {
      console.error('Failed to delete meme:', error);
      setMessage({ type: 'error', text: 'Failed to delete audio' });
    }
  };

  const startEdit = (meme) => {
    setEditingId(meme.id);
    setEditTags([...meme.tags]);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditTags([]);
  };

  const saveEdit = async (id) => {
    if (editTags.length === 0) {
      setMessage({ type: 'error', text: 'At least one tag is required' });
      return;
    }

    try {
      await apiService.updateMeme(id, editTags);
      setMessage({ type: 'success', text: 'Tags updated successfully' });
      setEditingId(null);
      await loadMemes();
    } catch (error) {
      console.error('Failed to update meme:', error);
      setMessage({ type: 'error', text: 'Failed to update tags' });
    }
  };

  if (loading) {
    return (
      <div className="text-center text-dark-muted">Loading library...</div>
    );
  }

  return (
    <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-6">Audio Library</h2>

      {/* Upload Section */}
      {!stagingMode ? (
        <div className="mb-6 pb-6 border-b border-dark-border">
          <label className="block text-sm font-medium mb-2">
            Upload Audio Files (MP3)
          </label>
          <input
            id="file-upload"
            type="file"
            accept=".mp3,audio/mpeg"
            multiple
            onChange={handleFileSelect}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-600 file:text-white hover:file:bg-green-700 file:cursor-pointer"
          />
          <p className="text-xs text-dark-muted mt-2">
            Select one or multiple MP3 files to upload
          </p>
        </div>
      ) : (
        /* Staging UI */
        <div className="mb-6 pb-6 border-b border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              Review Files ({pendingFiles.length})
            </h3>
            {uploading && (
              <span className="text-sm text-green-400">
                Uploading {uploadProgress.current} of {uploadProgress.total}...
              </span>
            )}
          </div>

          <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
            {pendingFiles.map((pending) => (
              <div
                key={pending.id}
                className="bg-dark-bg border border-dark-border rounded-lg p-4"
              >
                {/* Audio Preview */}
                <div className="mb-3">
                  <audio
                    controls
                    src={pending.audioUrl}
                    className="w-full h-10"
                    style={{ maxHeight: '40px' }}
                  />
                </div>

                {/* Filename Input */}
                <div className="mb-3">
                  <label className="block text-xs font-medium text-dark-muted mb-1">
                    Filename
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={pending.filename}
                      onChange={(e) => updatePendingFile(pending.id, { filename: e.target.value })}
                      className="flex-1 bg-dark-surface border border-dark-border rounded-lg px-3 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="Enter filename"
                    />
                    <span className="text-dark-muted">.mp3</span>
                  </div>
                </div>

                {/* Tags Input */}
                <div className="mb-3">
                  <label className="block text-xs font-medium text-dark-muted mb-1">
                    Tags (press comma to add)
                  </label>
                  <TagInput
                    tags={pending.tags}
                    onChange={(newTags) => updatePendingFile(pending.id, { tags: newTags })}
                    placeholder="e.g., you, I like you, great goal"
                  />
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => removePendingFile(pending.id)}
                  disabled={uploading}
                  className="w-full bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded-lg py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Remove File
                </button>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={confirmBulkUpload}
              disabled={uploading || pendingFiles.length === 0}
              className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-dark-border disabled:cursor-not-allowed rounded-lg py-3 font-semibold transition-colors"
            >
              {uploading ? `Uploading ${uploadProgress.current}/${uploadProgress.total}...` : `Confirm Import (${pendingFiles.length})`}
            </button>
            <button
              onClick={cancelStaging}
              disabled={uploading}
              className="flex-1 bg-dark-border hover:bg-dark-border/70 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg py-3 font-semibold transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Message */}
      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-900/20 border border-green-500 text-green-400'
            : 'bg-red-900/20 border border-red-500 text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* Meme List */}
      <div className="space-y-3">
        {memes.length === 0 ? (
          <p className="text-center text-dark-muted py-8">
            No audio files yet. Upload your first meme!
          </p>
        ) : (
          memes.map((meme) => (
            <div
              key={meme.id}
              className="bg-dark-bg border border-dark-border rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <p className="font-medium text-dark-text mb-1 break-all">
                    {meme.filename}
                  </p>

                  {editingId === meme.id ? (
                    <div>
                      <label className="block text-xs font-medium text-dark-muted mb-1">
                        Tags (press comma to add)
                      </label>
                      <TagInput
                        tags={editTags}
                        onChange={setEditTags}
                        placeholder="Type tag and press comma..."
                      />
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {meme.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="bg-green-900/30 text-green-400 px-2 py-0.5 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-dark-muted mb-3">
                <span>Played: {meme.play_count} times</span>
              </div>

              <div className="flex gap-2">
                {editingId === meme.id ? (
                  <>
                    <button
                      onClick={() => saveEdit(meme.id)}
                      className="flex-1 bg-green-600 hover:bg-green-700 rounded py-1.5 text-sm font-medium transition-colors"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="flex-1 bg-dark-border hover:bg-dark-border/70 rounded py-1.5 text-sm font-medium transition-colors"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => startEdit(meme)}
                      className="flex-1 bg-dark-border hover:bg-dark-border/70 rounded py-1.5 text-sm font-medium transition-colors"
                    >
                      Edit Tags
                    </button>
                    <button
                      onClick={() => handleDelete(meme.id)}
                      className="flex-1 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded py-1.5 text-sm font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
