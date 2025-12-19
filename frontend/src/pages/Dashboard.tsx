import React from 'react';

const Dashboard: React.FC = () => {
    console.log("[Dashboard] Rendered");
    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-white border-b border-eve-border pb-4">Captain's Quarters</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Wallet */}
                <div className="bg-eve-panel border border-eve-border p-4 rounded">
                    <h3 className="text-eve-muted text-sm uppercase">Wallet Balance</h3>
                    <p className="text-2xl font-mono text-eve-accent-blue mt-1">1,450,000,000 ISK</p>
                </div>

                {/* PLEX */}
                <div className="bg-eve-panel border border-eve-border p-4 rounded">
                    <h3 className="text-eve-muted text-sm uppercase">PLEX Vault</h3>
                    <p className="text-2xl font-mono text-eve-accent-orange mt-1">500 PLEX</p>
                </div>
            </div>

            <div className="bg-eve-panel border border-eve-border p-6 rounded h-96 flex items-center justify-center text-eve-muted">
                Skills Queue Visualization (Coming Soon)
            </div>
        </div>
    );
};

export default Dashboard;
