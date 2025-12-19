import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Placeholder Pages
const Market = () => <div className="text-2xl">Market View (Coming Soon)</div>;
const SearchPage = () => <div className="text-2xl">Search View (Coming Soon)</div>;
const Contracts = () => <div className="text-2xl">Contracts View (Coming Soon)</div>;

const router = createBrowserRouter([
    {
        path: "/login",
        element: <Login />
    },
    {
        path: "/",
        element: <MainLayout />,
        children: [
            { path: "/", element: <Navigate to="/dashboard" replace /> },
            { path: "dashboard", element: <Dashboard /> },
            { path: "market", element: <Market /> },
            { path: "search", element: <SearchPage /> },
            { path: "contracts", element: <Contracts /> },
        ]
    }
]);

export const AppRouter = () => {
    return <RouterProvider router={router} />;
};
