import { useAuth } from '../contexts/AuthContext';

export default function Dashboard() {
    const { session } = useAuth();

    return (
        <div style={{ padding: '2rem' }}>
            <h1>Dashboard</h1>
            <div className="card">
                <h2>Welcome, {session?.character_name}!</h2>
                <p>Character ID: <span className="text-mono">{session?.character_id}</span></p>
            </div>
        </div>
    );
}
