import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { CharacterSession } from '../types';

interface AuthContextType {
    session: CharacterSession | null;
    isAuthenticated: boolean;
    loading: boolean;
    login: () => void;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [session, setSession] = useState<CharacterSession | null>(null);
    const [loading, setLoading] = useState(true);

    // Check session on mount
    useEffect(() => {
        checkSession();
    }, []);

    const checkSession = async () => {
        try {
            const response = await fetch('/auth/session', {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    setSession(data);
                }
            }
        } catch (error) {
            console.error('Failed to check session:', error);
        } finally {
            setLoading(false);
        }
    };

    const login = () => {
        // Redirect to backend login endpoint
        window.location.href = '/auth/login';
    };

    const logout = async () => {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            setSession(null);
            window.location.href = '/login';
        } catch (error) {
            console.error('Failed to logout:', error);
        }
    };

    const value: AuthContextType = {
        session,
        isAuthenticated: session?.authenticated ?? false,
        loading,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
