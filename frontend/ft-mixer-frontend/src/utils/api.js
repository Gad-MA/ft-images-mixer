const BASE_URL = 'http://localhost:5000';

export const api = {
  uploadImage: async (slotId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BASE_URL}/upload/${slotId}`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  getView: async (slotId, type, component, brightness, contrast) => {
    // type is 'input' or 'output'. For output, slotId is portId (0 or 1).
    let endpoint;
    if (type === 'input') {
      endpoint = `${BASE_URL}/view/${slotId}/${component}`;
    } else {
      endpoint = `${BASE_URL}/output/${slotId}`;
    }
    
    const url = new URL(endpoint);
    url.searchParams.append('brightness', brightness);
    url.searchParams.append('contrast', contrast);
    
    const response = await fetch(url);
    return response.json();
  },

  startMixing: async (settings) => {
    const response = await fetch(`${BASE_URL}/mix`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return response.json();
  },

  getProgress: async () => {
    const response = await fetch(`${BASE_URL}/progress`);
    return response.json();
  },

  cancelMixing: async () => {
    const response = await fetch(`${BASE_URL}/cancel`, { method: 'POST' });
    return response.json();
  }
};