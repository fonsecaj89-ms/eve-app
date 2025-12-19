import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, ShoppingCart, Search, FileText, LogOut, Users } from 'lucide-react';
import { EveImage } from '../Common/EveImage';

// Mock User for Topbar (replace with context later)
const MOCK_USER = {
    id: 999999, // Needs real Fetch
    name: "Capsuleer"
};

const MainLayout: React.FC = () => {
    console.log("[MainLayout] Rendered");
    return (
        <div className="flex h-screen bg-eve-bg text-eve-text font-sans">
            {/* Sidebar */}
            <aside className="fixed left-0 top-0 h-full w-64 border-r border-eve-border bg-eve-panel p-4 flex flex-col">
                <div className="mb-8 flex items-center gap-2 px-2 text-eve-accent-blue">
                    <LayoutDashboard className="h-8 w-8" />
                    <span className="text-xl font-bold tracking-wider">NEOCOM</span>
                </div>

                <nav className="flex-1 space-y-2">
                    <NavLink to="/dashboard" className={({ isActive }) => `flex items-center gap-3 rounded px-4 py-3 transition-colors ${isActive ? 'bg-eve-accent-blue/20 text-white' : 'hover:bg-eve-border/50 text-eve-muted'}`}>
                        <Users size={20} /> Dashboard
                    </NavLink>
                    <NavLink to="/market" className={({ isActive }) => `flex items-center gap-3 rounded px-4 py-3 transition-colors ${isActive ? 'bg-eve-accent-blue/20 text-white' : 'hover:bg-eve-border/50 text-eve-muted'}`}>
                        <ShoppingCart size={20} /> Market
                    </NavLink>
                    <NavLink to="/search" className={({ isActive }) => `flex items-center gap-3 rounded px-4 py-3 transition-colors ${isActive ? 'bg-eve-accent-blue/20 text-white' : 'hover:bg-eve-border/50 text-eve-muted'}`}>
                        <Search size={20} /> Search
                    </NavLink>
                    <NavLink to="/contracts" className={({ isActive }) => `flex items-center gap-3 rounded px-4 py-3 transition-colors ${isActive ? 'bg-eve-accent-blue/20 text-white' : 'hover:bg-eve-border/50 text-eve-muted'}`}>
                        <FileText size={20} /> Contracts
                    </NavLink>
                </nav>

                <div className="mt-auto border-t border-eve-border pt-4">
                    <div className="flex items-center gap-3 px-2">
                        {/* Local Proxy Portrait */}
                        <EveImage type="character" id={MOCK_USER.id} className="h-10 w-10 rounded-full" />
                        <div className="flex-1 overflow-hidden">
                            <p className="truncate text-sm font-bold text-white">{MOCK_USER.name}</p>
                            <div className="flex items-center gap-1 text-xs text-green-500">
                                <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                                ESI OK
                            </div>
                        </div>
                        <button className="text-eve-muted hover:text-red-500" title="Logout">
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="ml-64 w-full p-8 overflow-y-auto">
                <Outlet />
            </main>
        </div>
    );
};

export default MainLayout;
