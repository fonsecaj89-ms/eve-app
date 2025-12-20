import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
    const { isAuthenticated, login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        // If already authenticated, redirect to dashboard or intended destination
        if (isAuthenticated) {
            const from = (location.state as any)?.from?.pathname || '/dashboard';
            navigate(from, { replace: true });
        }
    }, [isAuthenticated, navigate, location]);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            padding: '2rem'
        }}>
            <div className="card" style={{ maxWidth: '400px', textAlign: 'center' }}>
                <h1 style={{ marginBottom: '1.5rem' }}>EVE Trading Platform</h1>
                <p style={{ marginBottom: '2rem', color: 'var(--color-text-secondary)' }}>
                    High-frequency trading and industry analytics for EVE Online
                </p>
                <button
                    className="btn btn-primary"
                    onClick={login}
                    style={{ width: '100%', padding: '1rem' }}
                >
                    Login with EVE Online
                </button>
                <p style={{
                    marginTop: '1.5rem',
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-muted)'
                }}>
                    You will be redirected to EVE Online SSO for authentication
                </p>
            </div>
        </div>
    );
}
