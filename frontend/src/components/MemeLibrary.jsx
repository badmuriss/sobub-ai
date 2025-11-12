import { useState, useEffect } from 'react';
import apiService from '../services/api';

export default function MemeLibrary() {
  const [memes, setMemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editTags, setEditTags] = useState('');
  const [message, setMessage] = useState(null);

  // Upload form state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTags, setUploadTags] = useState('');

  useEffect(() => {
    loadMemes();
  }, []);

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

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!uploadFile || !uploadTags.trim()) {
      setMessage({ type: 'error', text: 'Please select a file and add tags' });
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      const tags = uploadTags.split(',').map(t => t.trim()).filter(t => t);
      await apiService.createMeme(uploadFile, tags);
      
      setMessage({ type: 'success', text: 'Audio uploaded successfully' });
      setUploadFile(null);
      setUploadTags('');
      
      // Reset file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) fileInput.value = '';
      
      await loadMemes();
    } catch (error) {
      console.error('Failed to upload meme:', error);
      setMessage({ type: 'error', text: 'Failed to upload audio' });
    } finally {
      setUploading(false);
    }
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
    setEditTags(meme.tags.join(', '));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditTags('');
  };

  const saveEdit = async (id) => {
    try {
      const tags = editTags.split(',').map(t => t.trim()).filter(t => t);
      await apiService.updateMeme(id, tags);
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

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="mb-6 pb-6 border-b border-dark-border">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Upload Audio (MP3)
          </label>
          <input
            id="file-upload"
            type="file"
            accept=".mp3,audio/mpeg"
            onChange={(e) => setUploadFile(e.target.files[0])}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-600 file:text-white hover:file:bg-green-700 file:cursor-pointer"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            value={uploadTags}
            onChange={(e) => setUploadTags(e.target.value)}
            placeholder="e.g. football, celebration, goal"
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        <button
          type="submit"
          disabled={uploading || !uploadFile}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-dark-border disabled:cursor-not-allowed rounded-lg py-2 font-semibold transition-colors"
        >
          {uploading ? 'Uploading...' : 'Upload Audio'}
        </button>
      </form>

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
                    <input
                      type="text"
                      value={editTags}
                      onChange={(e) => setEditTags(e.target.value)}
                      className="w-full bg-dark-surface border border-dark-border rounded px-2 py-1 text-sm"
                      placeholder="Tags (comma-separated)"
                    />
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
