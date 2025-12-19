import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0',
        port: 5173,
        hmr: {
            // Cloudflare Tunnel Support
            clientPort: 443,
            host: "eve-app.jf-nas.com"
        },
        allowedHosts: ["eve-app.jf-nas.com"]
    }
})
