// Auto-detect API URL based on where the frontend is accessed from
// With nginx reverse proxy, API is served from the same origin
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Use same origin as frontend (nginx routes /api/ to backend)
    return window.location.origin;
  }
  // Fallback for non-browser contexts (SSR, testing)
  return 'http://localhost';
};

const API_URL = getApiUrl();

class ApiService {
  async getMemes() {
    const response = await fetch(`${API_URL}/api/memes`);
    if (!response.ok) throw new Error('Failed to fetch memes');
    return response.json();
  }

  async getMeme(id) {
    const response = await fetch(`${API_URL}/api/memes/${id}`);
    if (!response.ok) throw new Error('Failed to fetch meme');
    return response.json();
  }

  async createMeme(file, tags) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tags', tags.join(', '));

    const response = await fetch(`${API_URL}/api/memes`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error('Failed to create meme');
    return response.json();
  }

  async updateMeme(id, tags) {
    const formData = new FormData();
    formData.append('tags', tags.join(', '));

    const response = await fetch(`${API_URL}/api/memes/${id}`, {
      method: 'PUT',
      body: formData,
    });

    if (!response.ok) throw new Error('Failed to update meme');
    return response.json();
  }

  async deleteMeme(id) {
    const response = await fetch(`${API_URL}/api/memes/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) throw new Error('Failed to delete meme');
    return response.json();
  }

  getMemeAudioUrl(id) {
    return `${API_URL}/api/memes/${id}/audio`;
  }

  async getSettings() {
    const response = await fetch(`${API_URL}/api/settings`);
    if (!response.ok) throw new Error('Failed to fetch settings');
    return response.json();
  }

  async updateSettings(settings) {
    const response = await fetch(`${API_URL}/api/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });

    if (!response.ok) throw new Error('Failed to update settings');
    return response.json();
  }

  async getStatus() {
    const response = await fetch(`${API_URL}/api/status`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return response.json();
  }

  async getAllTags() {
    const response = await fetch(`${API_URL}/api/tags`);
    if (!response.ok) throw new Error('Failed to fetch tags');
    return response.json();
  }
}

export default new ApiService();
