/**
 * Root application component for DocuSage.
 *
 * This file intentionally stays thin and only orchestrates layout, routing
 * between authenticated and guest views, and shared shell components.
 */

import React from 'react';
import './app.css';
import AuthForm from './components/AuthForm/AuthForm';
import Dashboard from './components/Dashboard/Dashboard';
import Navbar from './components/Navbar/Navbar';
import useAuth from './hooks/useAuth';

/**
 * Render the DocuSage application shell.
 */
const App = () => {
    const {
        token,
        userEmail,
        isAuthenticated,
        authError,
        isLoading,
        authenticate,
        logout,
    } = useAuth();

    return (
        <div className="app-main-layout">
            <Navbar
                isAuthenticated={isAuthenticated}
                userEmail={userEmail}
                logout={logout}
            />

            <main className="main-content">
                {isAuthenticated ? (
                    <Dashboard token={token} />
                ) : (
                    <AuthForm
                        authState={{ authError, isLoading }}
                        authenticate={authenticate}
                    />
                )}
            </main>
        </div>
    );
};

export default App;
