import axios from 'axios';

// Vite default is /, but we might need 8000 for local dev if not proxied?
// Prompt said: "HMR must work behind Cloudflare tunnel" and "Strictly use http://...:7777/api/images"
// docker-compose maps 7777 -> 5173 (frontend) and 8000 -> 8000 (backend).
// The frontend runs in browser.
// If using Tunnel, backend APIs should be accessible via relative path `/api` IF the tunnel handles Routing, 
// OR the frontend calls the backend URL directly.
// In local dev `http://localhost:8000`.
// Let's assume environment variable `VITE_API_URL` sets the base.
// In docker-compose, `VITE_API_URL` is passed.

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL,
    withCredentials: true, // Important for HttpOnly cookies (Session ID)
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config) => {
    console.log(`[API] Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
});

// Interceptors
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            const { status } = error.response;

            // 401: Unauthorized -> Logout
            if (status === 401) {
                console.warn("Session expired or unauthorized. Redirecting to login.");
                window.location.href = '/login';
            }

            // 429: Global Lockdown (Too Many Requests)
            if (status === 429) {
                // We should trigger a global modal state here.
                // For now, alert or dispatch event.
                console.error("GLOBAL LOCKDOWN: ESI Rate Limits Exceeded.");
                alert("GLOBAL LOCKDOWN ACTIVE. ESI Rate Limits Exceeded. Please wait.");
            }
        }
        return Promise.reject(error);
    }
);
