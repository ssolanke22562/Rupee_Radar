export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

if (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) {
  console.warn("WARNING: VITE_API_BASE_URL is not defined in production. API calls will default to localhost:8000.");
}

export async function apiClient<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}),
  } as HeadersInit;

  // Let fetch handle boundary for FormData
  if (options?.body instanceof FormData) {
    delete (headers as Record<string, string>)['Content-Type'];
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API call failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}
