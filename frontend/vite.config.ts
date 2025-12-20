import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0',  // Allow external container access
        port: 5173,
        strictPort: true,
        allowedHosts: ['eve-app.jf-nas.com', 'eve-frontend', 'localhost', '127.0.0.1'],

        // HMR configuration for Cloudflare Tunnel
        hmr: {
            protocol: 'wss',  // WebSocket Secure for tunnel
            host: 'eve-app.jf-nas.com',
            clientPort: 443  // HTTPS port
        },

        // File watching for Docker/WSL2
        watch: {
            usePolling: true,
            interval: 1000
        },

        // CRITICAL: Proxy configuration for EVE SSO callback
        proxy: {
            // EVE SSO callback - MUST proxy to backend for session storage
            '/callback': {
                target: 'http://backend-api:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/callback/, '/auth/callback')
            },

            // API routes
            '/api': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Auth routes
            '/auth': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Market routes
            '/market': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Contracts routes
            '/contracts': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Character routes
            '/character': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Universe routes
            '/universe': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            },

            // Routing routes
            '/routing': {
                target: 'http://backend-api:8000',
                changeOrigin: true
            }
        }
    },

    build: {
        outDir: 'dist',
        sourcemap: true
    }
})
