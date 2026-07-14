/**
 * This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.
 */

/**
 * Root application component for DocuSage.
 *
 * Orchestrates auth shell, theme, and the workspace layout.
 */

import React from 'react';
import './app.css';
import AuthForm from './components/AuthForm/AuthForm';
import TopBar from './components/TopBar/TopBar';
import Workspace from './components/Workspace/Workspace';
import useAuth from './hooks/useAuth';
import useTheme from './hooks/useTheme';

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

    const { theme, toggleTheme } = useTheme();

    return (
        <div className={`app-shell ${isAuthenticated ? 'is-authenticated' : 'is-guest'}`}>
            <TopBar
                isAuthenticated={isAuthenticated}
                userEmail={userEmail}
                token={token}
                logout={logout}
                theme={theme}
                onToggleTheme={toggleTheme}
            />

            <main className="app-main">
                {isAuthenticated ? (
                    <Workspace token={token} />
                ) : (
                    <div className="guest-wrap">
                        <AuthForm
                            authState={{ authError, isLoading }}
                            authenticate={authenticate}
                        />
                    </div>
                )}
            </main>
        </div>
    );
};

export default App;
