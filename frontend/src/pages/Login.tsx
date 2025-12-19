import React from 'react';
import { Shield } from 'lucide-react';

const Login: React.FC = () => {
    console.log("[Login] View Rendered");

    const handleLogin = () => {
        console.log("[Login] SSO Button Clicked");
        const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        console.log(`[Login] Redirecting to: ${baseURL}/auth/login`);
        window.location.href = `${baseURL}/auth/login`;
    };

    return (
        <div className="flex h-screen w-full items-center justify-center bg-eve-bg bg-[url('/bg-space.jpg')] bg-cover bg-center">
            <div className="relative z-10 w-96 rounded-lg border border-eve-border bg-eve-panel/90 p-8 text-center shadow-2xl backdrop-blur-md">
                <div className="mb-6 flex justify-center text-eve-accent-blue">
                    <Shield size={64} />
                </div>
                <h1 className="mb-2 text-3xl font-bold text-white tracking-widest">EVE TRADER</h1>
                <p className="mb-8 text-eve-muted">Secure Trading & Routing Platform</p>

                <button
                    onClick={handleLogin}
                    className="w-full flex items-center justify-center gap-2 rounded bg-[#F5A623] px-4 py-3 font-bold text-black transition-transform hover:scale-105 hover:bg-yellow-400"
                >
                    <img src="https://web.ccpgamescdn.com/eveonlineassets/developers/eve-sso-login-black-large.png" alt="SSO" className="h-6" />
                    LOGIN WITH EVE ONLINE
                </button>
            </div>
        </div>
    );
};

export default Login;
